import time
from typing import Dict, List


class InfractionState:
    def __init__(self, track_id: int, class_name: str):
        self.track_id = track_id
        self.class_name = class_name
        self.state = "advertencia"
        self.first_seen_time = time.time()
        self.TIME_THRESHOLD = 10.0
        self.alert_saved = False

    def update(self) -> str:
        current_time = time.time()
        elapsed_time = current_time - self.first_seen_time

        if elapsed_time >= self.TIME_THRESHOLD:
            self.state = "alerta"

        return self.state


class IncidentManager:
    def __init__(self):
        self.trackers: Dict[int, InfractionState] = {}

    def process_frame_detections(self, detections: List[dict]) -> List[dict]:
        processed_results = []
        current_ids = set()

        for det in detections:
            class_name = det["class_name"]
            track_id = det.get("track_id")

            if track_id is None or track_id == 0:
                det["status"] = "epp_detectado" if class_name in ["helmet", "vest"] else "advertencia"
                det["trigger_alert"] = False
                processed_results.append(det)
                continue

            if class_name in ["nohelmet", "novest"]:
                current_ids.add(track_id)

                if track_id not in self.trackers:
                    self.trackers[track_id] = InfractionState(track_id, class_name)

                state_obj = self.trackers[track_id]
                current_state = state_obj.update()

                trigger_db_alert = False

                if current_state == "alerta" and not state_obj.alert_saved:
                    trigger_db_alert = True
                    state_obj.alert_saved = True

                det["status"] = current_state
                det["trigger_alert"] = trigger_db_alert

                det["missing_epp"] = {
                    "helmet": class_name == "nohelmet",
                    "vest": class_name == "novest"
                }

            elif class_name in ["helmet", "vest"]:
                det["status"] = "epp_detectado"
                det["trigger_alert"] = False

            processed_results.append(det)

        ids_to_remove = [tid for tid in self.trackers if tid not in current_ids]
        for tid in ids_to_remove:
            del self.trackers[tid]

        return processed_results