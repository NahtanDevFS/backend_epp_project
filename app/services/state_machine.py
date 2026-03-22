import time
from typing import Dict, List
from app.services.geometry import is_ppe_on_person

class PersonState:
    def __init__(self, track_id: int):
        self.track_id = track_id
        self.state = "normal"
        self.missing_ppe_start_time = None
        self.TIME_THRESHOLD = 10.0
        self.alert_saved = False

    def update(self, has_ppe: bool) -> str:
        current_time = time.time()

        if has_ppe:
            self.state = "normal"
            self.missing_ppe_start_time = None
            self.alert_saved = False
        else:
            if self.state == "normal":
                self.state = "advertencia"
                self.missing_ppe_start_time = current_time
                self.alert_saved = False

            elif self.state == "advertencia":
                elapsed_time = current_time - self.missing_ppe_start_time
                if elapsed_time >= self.TIME_THRESHOLD:
                    self.state = "alerta"

        return self.state


class IncidentManager:
    def __init__(self):
        self.trackers: Dict[int, PersonState] = {}

    def process_frame_detections(self, detections: List[dict]) -> List[dict]:
        processed_results = []
        current_ids = set()

        people = [d for d in detections if d["class_name"] == "person"]

        helmets = [d for d in detections if d["class_name"] == "helmet"]
        vests = [d for d in detections if d["class_name"] == "vest"]

        for person_data in people:
            track_id = person_data.get("track_id")
            if track_id is None:
                continue

            current_ids.add(track_id)
            person_box = person_data["box"]

            if track_id not in self.trackers:
                self.trackers[track_id] = PersonState(track_id)

            has_helmet = any(is_ppe_on_person(h["box"], person_box) for h in helmets)
            has_vest = any(is_ppe_on_person(v["box"], person_box) for v in vests)

            has_ppe = has_helmet and has_vest

            person_state_obj = self.trackers[track_id]
            current_state = person_state_obj.update(has_ppe)

            trigger_db_alert = False

            if current_state == "alerta" and not person_state_obj.alert_saved:
                trigger_db_alert = True
                person_state_obj.alert_saved = True

            person_data["status"] = current_state
            person_data["trigger_alert"] = trigger_db_alert
            person_data["missing_epp"] = {
                "helmet": not has_helmet,
                "vest": not has_vest
            }

            processed_results.append(person_data)

        ids_to_remove = [tid for tid in self.trackers if tid not in current_ids]
        for tid in ids_to_remove:
            del self.trackers[tid]

        for h in helmets:
            h["status"] = "epp_detectado"
            processed_results.append(h)

        for v in vests:
            v["status"] = "epp_detectado"
            processed_results.append(v)

        return processed_results