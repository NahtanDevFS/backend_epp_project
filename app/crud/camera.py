from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models import Camera
from app.schemas.camera import CameraCreate

def get_camera(db: Session, camera_id: UUID):
    return db.query(Camera).filter(Camera.id == camera_id).first()

def get_cameras(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Camera).offset(skip).limit(limit).all()

def create_camera(db: Session, camera: CameraCreate):
    db_camera = Camera(
        location_name=camera.location_name,
        stream_url=camera.stream_url,
        status=camera.status
    )
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera