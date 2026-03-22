from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.schemas.camera import CameraCreate, CameraResponse
from app.crud import camera as crud_camera
from app.api.deps import get_current_user
from app.db.models import User

router = APIRouter(prefix="/cameras", tags=["Cameras"])

@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return crud_camera.create_camera(db=db, camera=camera)

@router.get("/", response_model=List[CameraResponse])
def read_cameras(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la lista de cámaras registradas.
    """
    cameras = crud_camera.get_cameras(db, skip=skip, limit=limit)
    return cameras

@router.get("/{camera_id}", response_model=CameraResponse)
def read_camera(
    camera_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    db_camera = crud_camera.get_camera(db, camera_id=camera_id)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    return db_camera