"""
Database Models Module

This module defines the SQLAlchemy ORM models for the RhinoGuardians application.
It includes models for storing detection results and their associated metadata.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
import enum
import uuid


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class AlertStatus(str, enum.Enum):
    """
    Enum for alert statuses.
    """
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    INACTIVE = "inactive"


class Detection(Base):
    __tablename__ = "detections"
    id = Column(Integer, primary_key=True)
    timestamp = Column(String)
    class_name = Column(String)
    confidence = Column(Float)
    image_path = Column(String)
    gps_lat = Column(Float)
    gps_lng = Column(Float)

    # Relationship with alerts
    alerts = relationship(
        "Alert",
        back_populates="detection",
        cascade="all, delete-orphan")


class Alert(Base):
    """
    Alert model for tracking notifications and status of critical detections.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True,
                comment="Internal numeric PK for the alert")
    alert_id = Column(
        String,
        unique=True,
        nullable=False,
        comment="External identifier for the alert (used in PATCH)")
    detection_id = Column(Integer,
                          ForeignKey("detections.id", ondelete="CASCADE"),
                          nullable=False,
                          comment="ID of the associated detection")
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow,
                       comment="When the alert was created")
    status = Column(
        Enum(AlertStatus),
        nullable=False,
        default=AlertStatus.ACTIVE,
        comment="Current status of the alert")
    type = Column(String, nullable=False,
                  comment="Type of alert (e.g., poacher_suspected)")
    severity = Column(String, nullable=False,
                      comment="Alert severity level")
    source = Column(String, nullable=False,
                    comment="Source of the alert (e.g., camera_trap)")
    notes = Column(String, nullable=True,
                   comment="Optional operator notes")
    lat = Column(Float, nullable=True,
                 comment="Latitude of alert location")
    lng = Column(Float, nullable=True,
                 comment="Longitude of alert location")
    zone_label = Column(String, nullable=True,
                        comment="Label of the zone where alert was triggered")
    created_by = Column(String, nullable=True,
                        comment="Operator who created the alert")
    notification_sent = Column(Boolean, default=False,
                               comment="Whether notification was sent")
    notification_timestamp = Column(DateTime, nullable=True,
                                    comment="When notification was sent")
    message = Column(String, nullable=True,
                     comment="Alert message or description")
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="When the alert was last updated")

    # Relationship back to Detection
    detection = relationship("Detection", back_populates="alerts")

    __table_args__ = (
        {
            "comment": "Table for storing alerts related to rhino detections"
        },
    )

    @staticmethod
    def generate_alert_id():
        """Generate a unique alert_id for each alert."""
        return f"RG-{uuid.uuid4().hex[:8]}"
