from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.detector import PPEDetector
from app.services.state_machine import IncidentManager
from app.core import security
import jwt
import time
import cv2
import os
import uuid
import asyncio
import base64
import threading
from uuid import UUID

from app.db.database import SessionLocal
from app.crud import alert as crud_alert
from app.schemas.alert import AlertCreate, AlertDetailCreate
from app.db.models import AlertStatus, EPPClass, Camera

os.makedirs("static/evidences", exist_ok=True)

router = APIRouter()


class ThreadedCamera:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        if isinstance(src, str) and src.startswith("http"):
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.ret, self.frame = self.cap.read()
        self.stopped = False

        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                self.stopped = True
            else:
                self.ret = ret
                self.frame = frame

    def read(self):
        if self.frame is not None:
            return self.ret, self.frame.copy()
        return self.ret, None

    def release(self):
        self.stopped = True
        if self.thread.is_alive():
            self.thread.join(timeout=1)
        self.cap.release()


@router.websocket("/ws/video-stream/{camera_id}")
async def video_stream_endpoint(websocket: WebSocket, camera_id: UUID, token: str = Query(None)):
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
    print(f"Supervisor '{username}' conectado al flujo de la cámara {camera_id}.")

    db = SessionLocal()
    camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not camera or not camera.stream_url:
        await websocket.send_json({"status": "error", "message": "Cámara no encontrada o sin URL"})
        await websocket.close()
        db.close()
        return

    stream_source = camera.stream_url

    if stream_source.isdigit():
        stream_source = int(stream_source)
    elif isinstance(stream_source, str):
        stream_source = stream_source.strip()
        if not stream_source.startswith(("http://", "https://", "rtsp://")):
            stream_source = f"http://{stream_source}"

    cap = ThreadedCamera(stream_source)

    ppe_detector = PPEDetector()
    incident_manager = IncidentManager()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                await websocket.send_json({"status": "error", "message": "Señal de video perdida"})
                await asyncio.sleep(2)
                cap.release()
                cap = ThreadedCamera(stream_source)
                continue

            start_time = time.time()
            orig_height, orig_width, _ = frame.shape

            raw_detections = ppe_detector.detect_objects(frame)
            processed_detections = incident_manager.process_frame_detections(raw_detections)

            scale_x = 640 / orig_width
            scale_y = 480 / orig_height

            for det in processed_detections:
                x, y, w, h = det["box"]
                det["box"] = [
                    round(x * scale_x, 2),
                    round(y * scale_y, 2),
                    round(w * scale_x, 2),
                    round(h * scale_y, 2)
                ]

                if det.get("trigger_alert") and camera:
                    filename = f"{uuid.uuid4()}.jpg"
                    filepath = os.path.join("static/evidences", filename)
                    cv2.imwrite(filepath, frame)

                    alert_data = AlertCreate(
                        camera_id=camera.id,
                        evidence_url=f"/static/evidences/{filename}",
                        duration_seconds=10,
                        status=AlertStatus.PENDING,
                        details=[
                            AlertDetailCreate(epp_type=EPPClass.HELMET, is_missing=det["missing_epp"]["helmet"]),
                            AlertDetailCreate(epp_type=EPPClass.VEST, is_missing=det["missing_epp"]["vest"])
                        ]
                    )
                    crud_alert.create_alert(db=db, alert=alert_data)

            frame_resized = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 50])
            base64_image = base64.b64encode(buffer).decode('utf-8')

            process_time = (time.time() - start_time) * 1000

            await websocket.send_json({
                "status": "success",
                "resolution": "640x480",
                "process_time_ms": round(process_time, 2),
                "detections": processed_detections,
                "image": base64_image
            })

            await asyncio.sleep(0.001)

    except WebSocketDisconnect:
        print(f"El cliente se ha desconectado de la cámara {camera_id}")
    except Exception as e:
        print(f"Error inesperado en WebSocket ({camera_id}): {e}")
    finally:
        incident_manager.trackers.clear()
        cap.release()
        db.close()