from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models import Camera
from app.schemas.camera import CameraCreate
from app.schemas.camera import CameraUpdate

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

def update_camera(db: Session, camera_id: UUID, camera_update: CameraUpdate):
    db_camera = get_camera(db, camera_id)
    if db_camera:
        update_data = camera_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_camera, key, value)
        db.commit()
        db.refresh(db_camera)
    return db_camera

def delete_camera(db: Session, camera_id: UUID):
    db_camera = get_camera(db, camera_id)
    if db_camera:
        db.delete(db_camera)
        db.commit()
    return db_camera