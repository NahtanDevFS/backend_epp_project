import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"

class CameraStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class AlertStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"

class EPPClass(str, enum.Enum):
    HELMET = "helmet"
    VEST = "vest"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_name = Column(String(100), nullable=False)
    stream_url = Column(Text, nullable=True)
    status = Column(Enum(CameraStatus), default=CameraStatus.INACTIVE)
    last_online = Column(DateTime, nullable=True)

    alerts = relationship("Alert", back_populates="camera", cascade="all, delete-orphan")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    evidence_url = Column(Text, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.PENDING)

    camera = relationship("Camera", back_populates="alerts")
    details = relationship("AlertDetail", back_populates="alert", cascade="all, delete-orphan")

class AlertDetail(Base):
    __tablename__ = "alert_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=False)
    epp_type = Column(Enum(EPPClass), nullable=False)
    is_missing = Column(Boolean, nullable=False, default=True)

    alert = relationship("Alert", back_populates="details")