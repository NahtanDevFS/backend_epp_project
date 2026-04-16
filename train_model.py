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
        epochs=60,
        imgsz=640,
        batch=16,
        device=0,
        workers=4,
        project="ia_models",
        name="ppe_detector_v13",

        auto_augment=False,

        #aumentaciones anti sesgo de color
        hsv_h=0.05,       #varía el tono
        hsv_s=0.9,        #varía saturación fuertemente
        hsv_v=0.5,        #varía brillo
        erasing=0.3,      #borra regiones aleatorias

        #aumentaciones de contexto
        scale=0.5,         #zoom in/out
        fliplr=0.5,        #espejo horizontal
        degrees=10.0,      #rotación leve

        patience=15,       #detiene si no mejora en 15 épocas (evita sobreajuste)
        cos_lr=True,       #learning rate coseno — converge más suavemente
        plots=True
    )

    print("\nEntrenamiento finalizado")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    train_ppe_model()