from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.vision import decode_image
from app.services.detector import detect_objects
from app.services.state_machine import IncidentManager
from app.core import security
import jwt
import time
import cv2
import os
import uuid

from app.db.database import SessionLocal
from app.crud import alert as crud_alert
from app.schemas.alert import AlertCreate, AlertDetailCreate
from app.db.models import AlertStatus, EPPClass, Camera

os.makedirs("static/evidences", exist_ok=True)

router = APIRouter()

incident_manager = IncidentManager()


@router.websocket("/ws/video-stream")
async def video_stream_endpoint(websocket: WebSocket, token: str = Query(None)):
    if token is None:
        await websocket.close(code=1008, reason="Token faltante")
        return

    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=1008, reason="Token inválido")
            return
    except jwt.PyJWTError:
        await websocket.close(code=1008, reason="Token expirado o corrupto")
        return

    await websocket.accept()
    print(f"Supervisor '{username}' conectado al flujo de video.")

    db = SessionLocal()

    camera = db.query(Camera).first()
    if not camera:
        print("ADVERTENCIA: No hay cámaras en la base de datos. La alerta fallará.")

    try:
        while True:

            data = await websocket.receive_text()

            start_time = time.time()

            frame = decode_image(data)

            if frame is not None:
                height, width, _ = frame.shape

                raw_detections = detect_objects(frame)

                processed_detections = incident_manager.process_frame_detections(raw_detections)

                for det in processed_detections:
                    if det.get("trigger_alert") and camera:
                        # 1. Guardar la evidencia física
                        filename = f"{uuid.uuid4()}.jpg"
                        filepath = os.path.join("static/evidences", filename)
                        cv2.imwrite(filepath, frame)
                        print(f"📸 Evidencia guardada en: {filepath}")

                        alert_data = AlertCreate(
                            camera_id=camera.id,
                            evidence_url=f"/static/evidences/{filename}",
                            duration_seconds=10,
                            status=AlertStatus.PENDING,
                            details=[
                                AlertDetailCreate(epp_type=EPPClass.HELMET, is_missing=True),
                                AlertDetailCreate(epp_type=EPPClass.VEST, is_missing=True)
                            ]
                        )

                        crud_alert.create_alert(db=db, alert=alert_data)
                        print("Alerta insertada en PostgreSQL correctamente.")

                process_time = (time.time() - start_time) * 1000

                await websocket.send_json({
                    "status": "success",
                    "resolution": f"{width}x{height}",
                    "process_time_ms": round(process_time, 2),
                    "detections": processed_detections
                })
            else:
                await websocket.send_json({
                    "status": "error",
                    "message": "Fotograma corrupto o ilegible"
                })

    except WebSocketDisconnect:
        print("El cliente se ha desconectado")
        incident_manager.trackers.clear()
    except Exception as e:
        print(f"Error inesperado en WebSocket: {e}")
    finally:
        db.close()