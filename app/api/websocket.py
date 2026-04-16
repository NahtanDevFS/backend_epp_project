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
from app.db.models import AlertStatus, EPPClass, Camera, User
from app.services.email import send_alert_email

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

    try:
        cap = await asyncio.to_thread(ThreadedCamera, stream_source)
    except Exception as e:
        await websocket.send_json({"status": "error", "message": f"Fallo crítico al conectar cámara: {e}"})
        await websocket.close()
        db.close()
        return

    ppe_detector = PPEDetector()
    incident_manager = IncidentManager()

    target_fps = 10  #limitar el envío a 12 FPS
    frame_interval = 1.0 / target_fps
    last_send_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                await websocket.send_json(
                    {"status": "error", "message": "Señal de video perdida o cámara fuera de línea"})
                await asyncio.sleep(2)

                await asyncio.to_thread(cap.release)
                try:
                    cap = await asyncio.to_thread(ThreadedCamera, stream_source)
                except Exception:
                    pass
                continue

            start_time = time.time()
            orig_height, orig_width, _ = frame.shape

            raw_detections = await asyncio.to_thread(ppe_detector.detect_objects, frame)

            processed_detections = incident_manager.process_frame_detections(raw_detections)

            scale_x = 640 / orig_width
            scale_y = 480 / orig_height

            for det in processed_detections:
                x_center, y_center, w, h = det["box"]

                if det.get("trigger_alert") and camera:
                    filename = f"{uuid.uuid4()}.jpg"
                    filepath = os.path.join("static/evidences", filename)

                    #lógica de recorte cuerpo completo + padding
                    padding = 50  #píxeles extra para que se vea el contexto alrededor
                    y1 = int(y_center - (h / 2)) - padding
                    y2 = int(y_center + (h / 2)) + padding
                    x1 = int(x_center - (w / 2)) - padding
                    x2 = int(x_center + (w / 2)) + padding

                    #asegurar que las coordenadas no salgan del tamaño de la imagen
                    x1 = max(0, x1)
                    y1 = max(0, y1)
                    x2 = min(orig_width, x2)
                    y2 = min(orig_height, y2)

                    cropped_frame = frame[y1:y2, x1:x2].copy()

                    if cropped_frame.size > 0:
                        #calcular coordenadas de la caja relativas al recorte
                        box_x1_orig = int(x_center - w / 2)
                        box_y1_orig = int(y_center - h / 2)
                        box_x2_orig = int(x_center + w / 2)
                        box_y2_orig = int(y_center + h / 2)

                        box_x1 = box_x1_orig - x1
                        box_y1 = box_y1_orig - y1
                        box_x2 = box_x2_orig - x1
                        box_y2 = box_y2_orig - y1

                        color = (0, 0, 255)  #rojo
                        cv2.rectangle(cropped_frame, (box_x1, box_y1), (box_x2, box_y2), color, 2)

                        if det["class_name"] == "unsafe":
                            label = "SIN CASCO NI CHALECO"
                        elif det["class_name"] == "no helmet":
                            label = "FALTA CASCO"
                        else:
                            label = "FALTA CHALECO"

                        text_y = max(20, box_y1 - 10)
                        cv2.putText(cropped_frame, label, (box_x1, text_y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                        await asyncio.to_thread(cv2.imwrite, filepath, cropped_frame)
                    else:
                        await asyncio.to_thread(cv2.imwrite, filepath, frame)

                    missing_details = []
                    if det["missing_epp"]["helmet"]:
                        missing_details.append(AlertDetailCreate(epp_type=EPPClass.HELMET, is_missing=True))
                    if det["missing_epp"]["vest"]:
                        missing_details.append(AlertDetailCreate(epp_type=EPPClass.VEST, is_missing=True))

                    alert_data = AlertCreate(
                        camera_id=camera.id,
                        evidence_url=f"/static/evidences/{filename}",
                        duration_seconds=10,
                        status=AlertStatus.PENDING,
                        details=missing_details
                    )
                    crud_alert.create_alert(db=db, alert=alert_data)

                    supervisor = db.query(User).filter(User.username == username).first()

                    if supervisor and supervisor.email:
                        asyncio.create_task(
                            asyncio.to_thread(
                                send_alert_email,
                                destinatario=supervisor.email,
                                camera_location=camera.location_name,
                                missing_helmet=det["missing_epp"]["helmet"],
                                missing_vest=det["missing_epp"]["vest"]
                            )
                        )

                det["box"] = [
                    round(x_center * scale_x, 2),
                    round(y_center * scale_y, 2),
                    round(w * scale_x, 2),
                    round(h * scale_y, 2)
                ]

            frame_resized = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 50])
            base64_image = base64.b64encode(buffer).decode('utf-8')

            current_time = time.time()
            #solo codificar y enviar si ha pasado el tiempo necesario (1/12 de segundo)
            if (current_time - last_send_time) >= frame_interval:
                frame_resized = cv2.resize(frame, (640, 480))
                #baja la calidad JPEG de 50 a 35
                _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 35])
                base64_image = base64.b64encode(buffer).decode('utf-8')

                process_time = (time.time() - start_time) * 1000

                await websocket.send_json({
                    "status": "success",
                    "resolution": "640x480",
                    "process_time_ms": round(process_time, 2),
                    "detections": processed_detections,
                    "image": base64_image
                })

                last_send_time = time.time()

            await asyncio.sleep(0.001)

    except WebSocketDisconnect:
        print(f"El cliente se ha desconectado de la cámara {camera_id}")
    except Exception as e:
        print(f"Error inesperado en WebSocket ({camera_id}): {e}")
    finally:
        incident_manager.trackers.clear()
        await asyncio.to_thread(cap.release)
        db.close()