from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from app.db.models import Alert, AlertDetail
from app.schemas.alert import AlertCreate


def get_alert(db: Session, alert_id: UUID):
    return db.query(Alert).filter(Alert.id == alert_id).first()


def get_alerts(db: Session, skip: int = 0, limit: int = 100, camera_id: str = None, status: str = None,
               date_from: datetime = None, date_to: datetime = None):
    query = db.query(Alert)

    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    if status:
        query = query.filter(Alert.status == status)
    if date_from:
        query = query.filter(Alert.timestamp >= date_from)
    if date_to:
        query = query.filter(Alert.timestamp <= date_to)

    return query.order_by(Alert.timestamp.desc()).offset(skip).limit(limit).all()


def create_alert(db: Session, alert: AlertCreate):
    db_alert = Alert(
        camera_id=alert.camera_id,
        evidence_url=alert.evidence_url,
        duration_seconds=alert.duration_seconds,
        status=alert.status,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)

    for detail in alert.details:
        db_detail = AlertDetail(
            alert_id=db_alert.id,
            epp_type=detail.epp_type,
            is_missing=detail.is_missing
        )
        db.add(db_detail)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def delete_alert(db: Session, alert_id: UUID):
    db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if db_alert:
        db.delete(db_alert)
        db.commit()
    return db_alert