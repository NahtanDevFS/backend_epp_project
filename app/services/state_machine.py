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

    def _boxes_overlap(self, box1: list, box2: list, threshold=0.5) -> bool:
        x1_c, y1_c, w1, h1 = box1
        x2_c, y2_c, w2, h2 = box2

        x1_min, y1_min = x1_c - w1 / 2, y1_c - h1 / 2
        x1_max, y1_max = x1_c + w1 / 2, y1_c + h1 / 2

        x2_min, y2_min = x2_c - w2 / 2, y2_c - h2 / 2
        x2_max, y2_max = x2_c + w2 / 2, y2_c + h2 / 2

        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)

        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return False

        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        area1 = w1 * h1

        return (inter_area / area1) > threshold

    def _resolve_conflicts(self, detections: List[dict]) -> List[dict]:
        positives = [d for d in detections if d["class_name"] in ["helmet", "vest"]]
        negatives = [d for d in detections if d["class_name"] in ["nohelmet", "novest"]]

        valid_detections = positives.copy()

        for neg in negatives:
            is_false_positive = False
            for pos in positives:
                if (neg["class_name"] == "novest" and pos["class_name"] == "vest") or \
                        (neg["class_name"] == "nohelmet" and pos["class_name"] == "helmet"):
                    if self._boxes_overlap(neg["box"], pos["box"]):
                        is_false_positive = True
                        break

            if not is_false_positive:
                valid_detections.append(neg)

        return valid_detections

    def process_frame_detections(self, raw_detections: List[dict]) -> List[dict]:
        detections = self._resolve_conflicts(raw_detections)

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