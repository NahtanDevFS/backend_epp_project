from ultralytics import YOLO
import os


def evaluate_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "runs", "detect", "ia_models", "ppe_detector_v12", "weights", "best.pt")
    yaml_path = os.path.join(current_dir, "datasets", "PPE-Updated-3", "data.yaml")

    model = YOLO(model_path)

    print("Evaluando el modelo con el conjunto de prueba (test)...")

    metrics = model.val(
        data=yaml_path,
        split='test',
        plots=True,
        project="ia_models",
        name="ppe_evaluation"
    )

    print("\nEvaluación completada en la carpeta: ia_models/ppe_evaluation/")


if __name__ == "__main__":
    evaluate_model()