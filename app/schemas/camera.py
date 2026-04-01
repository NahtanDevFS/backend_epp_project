from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.db.models import CameraStatus

class CameraBase(BaseModel):
    location_name: str
    stream_url: Optional[str] = None
    status: CameraStatus = CameraStatus.INACTIVE

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    id: UUID
    last_online: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class CameraUpdate(BaseModel):
    location_name: Optional[str] = None
    stream_url: Optional[str] = None
    status: Optional[CameraStatus] = None