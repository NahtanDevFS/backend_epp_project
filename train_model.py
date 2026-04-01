import os
import multiprocessing
from ultralytics import YOLO

def train_ppe_model():
    print("Iniciando preparación del modelo...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, "datasets", "20250731-ppe2286y", "data.yaml")

    model = YOLO("yolo11n.pt")

    print("Iniciando entrenamiento en la RTX 2060...")
    results = model.train(
        data=yaml_path,
        epochs=50,
        imgsz=640,
        batch=16,
        device=0,
        workers=4,
        project="ia_models",
        name="ppe_detector_v11",
        plots=True
    )

    print("\nEntrenamiento finalizado")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    train_ppe_model()