from ultralytics import YOLO


def train_ppe_model():
    print("Iniciando preparación del modelo...")

    model = YOLO("yolov8n.pt")

    print("Iniciando entrenamiento en la RTX 2060...")
    results = model.train(
        data="Construction-PPE.yaml",
        epochs=50,
        imgsz=640,
        batch=16,
        device=0,
        workers=4,
        project="ia_models",
        name="ppe_detector_v1",
        plots=True
    )

    print("\nEntrenamiento finalizado")
    print("El modelo listo para producción se guardó en: ia_models/ppe_detector_v1/weights/best.pt")


if __name__ == "__main__":
    # Esta validación es obligatoria en Windows cuando usamos multiprocesamiento (workers > 0)
    import multiprocessing

    multiprocessing.freeze_support()
    train_ppe_model()