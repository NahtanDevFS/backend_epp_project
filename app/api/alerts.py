from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.db.database import get_db
from app.schemas.alert import AlertCreate, AlertResponse
from app.crud import alert as crud_alert
from app.api.deps import get_current_user
from app.db.models import User

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Bloqueo de seguridad
):

    return crud_alert.create_alert(db=db, alert=alert)

@router.get("/", response_model=List[AlertResponse])
def read_alerts(
    skip: int = 0,
    limit: int = 100,
    camera_id: Optional[UUID] = None,
    alert_status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alerts = crud_alert.get_alerts(
        db,
        skip=skip,
        limit=limit,
        camera_id=camera_id,
        status=alert_status,
        date_from=date_from,
        date_to=date_to
    )
    return alerts

@router.get("/{alert_id}", response_model=AlertResponse)
def read_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    db_alert = crud_alert.get_alert(db, alert_id=alert_id)
    if db_alert is None:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return db_alert

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted = crud_alert.delete_alert(db, alert_id=alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return None