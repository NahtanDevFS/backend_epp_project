import cv2
import numpy as np
import base64


def decode_image(data: str | bytes) -> np.ndarray:

    try:

        if isinstance(data, str) and "," in data:
            data = data.split(",")[1]

        img_bytes = base64.b64decode(data)

        np_arr = np.frombuffer(img_bytes, np.uint8)

        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("OpenCV no pudo decodificar la imagen.")

        return img

    except Exception as e:
        print(f"Error decodificando el fotograma: {e}")
        return None