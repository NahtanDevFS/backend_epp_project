from ultralytics import YOLO
import numpy as np

class PPEDetector:
    def __init__(self):
        self.model = YOLO("best.pt")
        self.allowed_classes = {"safe", "unsafe", "no helmet", "no jacket"}

    def detect_objects(self, frame: np.ndarray):
        results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)

        detections = []

        for result in results:
            if result.boxes is None or len(result.boxes) == 0:
                continue

            boxes = result.boxes.xywh.cpu().tolist()
            clss = result.boxes.cls.int().cpu().tolist()
            confs = result.boxes.conf.float().cpu().tolist()

            if result.boxes.id is not None:
                track_ids = result.boxes.id.int().cpu().tolist()
            else:
                track_ids = [0] * len(boxes)

            for track_id, box, cls, conf in zip(track_ids, boxes, clss, confs):
                if conf > 0.4:
                    raw_class_name = self.model.names[cls]
                    normalized_class_name = raw_class_name.lower()

                    if normalized_class_name not in self.allowed_classes:
                        continue

                    detections.append({
                        "track_id": track_id,
                        "class_id": cls,
                        "class_name": normalized_class_name,
                        "confidence": round(conf, 2),
                        "box": [round(coord, 2) for coord in box]
                    })

        return detections