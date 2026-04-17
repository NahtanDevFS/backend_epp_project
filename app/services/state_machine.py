import time
from typing import Dict, List

class InfractionState:
    def __init__(self, track_id: int, class_name: str):
        self.track_id = track_id
        self.class_name = class_name
        self.state = "advertencia"
        self.first_seen_time = time.time()
        self.last_seen_time = self.first_seen_time
        self.TIME_THRESHOLD = 10.0
        self.alert_saved = False

    def update(self) -> str:
        current_time = time.time()
        self.last_seen_time = current_time
        elapsed_time = current_time - self.first_seen_time

        if elapsed_time >= self.TIME_THRESHOLD:
            self.state = "alerta"

        return self.state

class IncidentManager:
    def __init__(self):
        self.trackers: Dict[int, InfractionState] = {}
        self.grace_period = 5.0

    def process_frame_detections(self, raw_detections: List[dict]) -> List[dict]:
        detections = raw_detections
        processed_results = []
        current_ids = set()

        for det in detections:
            class_name = det["class_name"]
            track_id = det.get("track_id")

            #si no hay track_id, no podemos hacer seguimiento en el tiempo
            if track_id is None or track_id == 0:
                det["status"] = "epp_detectado" if class_name == "safe" else "advertencia"
                det["trigger_alert"] = False
                processed_results.append(det)
                continue

            #clases de infracción
            if class_name in ["unsafe", "no helmet", "no jacket"]:
                current_ids.add(track_id)

                if track_id not in self.trackers:
                    self.trackers[track_id] = InfractionState(track_id, class_name)

                state_obj = self.trackers[track_id]
                #actualiza la clase por si el modelo detectó un cambio
                state_obj.class_name = class_name
                current_state = state_obj.update()

                trigger_db_alert = False

                if current_state == "alerta" and not state_obj.alert_saved:
                    trigger_db_alert = True
                    state_obj.alert_saved = True

                det["status"] = current_state
                det["trigger_alert"] = trigger_db_alert

                #mapeo directo para la base de datos
                det["missing_epp"] = {
                    "helmet": class_name in ["no helmet", "unsafe"],
                    "vest": class_name in ["no jacket", "unsafe"]
                }

            #trabajador cumple con el equipo
            elif class_name == "safe":
                det["status"] = "epp_detectado"
                det["trigger_alert"] = False

            processed_results.append(det)

        #lógica de limpieza con paciencia
        current_time = time.time()
        ids_to_remove = []

        for tid, state in self.trackers.items():
            if tid not in current_ids:
                time_unseen = current_time - state.last_seen_time
                if time_unseen > self.grace_period:
                    ids_to_remove.append(tid)

        for tid in ids_to_remove:
            del self.trackers[tid]

        return processed_results