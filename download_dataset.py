from roboflow import Roboflow
import os

os.makedirs("datasets", exist_ok=True)
os.chdir("datasets")

rf = Roboflow(api_key="QqIS2rHD8qSwjrbx2abW")
project = rf.workspace("roboflow-universe-projects").project("construction-site-safety")
version = project.version(28)
dataset = version.download("yolov11")

print(f"Dataset descargado en: datasets/{dataset.location}")