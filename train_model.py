import os
import multiprocessing
from ultralytics import YOLO

def train_ppe_model():
    print("Iniciando preparación del modelo...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, "datasets", "PPE-Updated-3", "data.yaml")

    model = YOLO("yolo11s.pt")

    print("Iniciando entrenamiento en la RTX 2060...")
    results = model.train(
        data=yaml_path,
        epochs=100,
        imgsz=640,
        batch=16,
        device=0,
        workers=4,
        project="ia_models",
        name="ppe_detector_v12",
        plots=True
    )

    print("\nEntrenamiento finalizado")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    train_ppe_model()