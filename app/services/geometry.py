def xywh_to_xyxy(box: list) -> list:
    x_c, y_c, w, h = box
    return [x_c - w / 2, y_c - h / 2, x_c + w / 2, y_c + h / 2]


def get_intersection_area(box1_xyxy: list, box2_xyxy: list) -> float:
    x_left = max(box1_xyxy[0], box2_xyxy[0])
    y_top = max(box1_xyxy[1], box2_xyxy[1])
    x_right = min(box1_xyxy[2], box2_xyxy[2])
    y_bottom = min(box1_xyxy[3], box2_xyxy[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    return (x_right - x_left) * (y_bottom - y_top)


def is_ppe_on_person(ppe_box: list, person_box: list, threshold: float = 0.6) -> bool:
    ppe_xyxy = xywh_to_xyxy(ppe_box)
    person_xyxy = xywh_to_xyxy(person_box)

    inter_area = get_intersection_area(ppe_xyxy, person_xyxy)

    ppe_area = (ppe_xyxy[2] - ppe_xyxy[0]) * (ppe_xyxy[3] - ppe_xyxy[1])

    if ppe_area == 0:
        return False

    return (inter_area / ppe_area) >= threshold