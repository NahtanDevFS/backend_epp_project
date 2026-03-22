from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.db.models import AlertStatus, EPPClass


class AlertDetailBase(BaseModel):
    epp_type: EPPClass
    is_missing: bool = True


class AlertDetailCreate(AlertDetailBase):
    pass


class AlertDetailResponse(AlertDetailBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class AlertBase(BaseModel):
    camera_id: UUID
    evidence_url: str
    duration_seconds: int
    status: AlertStatus = AlertStatus.PENDING


class AlertCreate(AlertBase):
    details: List[AlertDetailCreate]


class AlertResponse(AlertBase):
    id: UUID
    timestamp: datetime
    details: List[AlertDetailResponse]

    model_config = ConfigDict(from_attributes=True)