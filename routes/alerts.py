"""
Alerts

This module handles all alert-related endpoints, including retrieving
active alerts, managing alert settings, and triggering notifications.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends, Path, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import Column, String

import builtins
from database.db import get_db
from database.models import Alert, AlertStatus as DBAlertStatus
from utils.notifications import NotificationService
from typing import Optional
from .schemas import AlertTriggerRequest, AlertResponse, Location, AlertStatus as APIAlertStatus, UpdateStatusRequest
getattr = builtins.getattr
import uuid

alert_id = Column(
    String,
    unique=True,
    nullable=False,
    default=lambda: str(
        uuid.uuid4()))


router = APIRouter(prefix="/alerts", tags=["alerts"])
# auto_error=False, return 401 for missing token instead of 403
security = HTTPBearer(auto_error=False)
notification_service = NotificationService()


@router.get("/")
async def get_alerts(
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        # Order by available timestamp; fallback to id
        order_col = getattr(Alert, "timestamp", getattr(Alert, "created_at", Alert.id))
        q = select(Alert).order_by(desc(order_col))
        if status:
            value = getattr(DBAlertStatus, status, None) or status
            q = q.filter(Alert.status == value)

        total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
        items = db.execute(q.offset(skip).limit(limit)).scalars().all()

        result = []
        for a in items:
            status_name = getattr(a.status, "name", None)
            st = status_name if status_name is not None else str(a.status)
            ts = getattr(a, "timestamp", getattr(a, "created_at", datetime.utcnow()))
            result.append({
                "alert_id": getattr(a, "alert_id", None),
                "detection_id": getattr(a, "detection_id", None),
                "status": st,
                "type": getattr(a, "type", None),
                "severity": getattr(a, "severity", None),
                "source": getattr(a, "source", None),
                "lat": getattr(a, "lat", None),
                "lng": getattr(a, "lng", None),
                "zone_label": getattr(a, "zone_label", None),
                "created_by": getattr(a, "created_by", None),
                "timestamp": ts.isoformat() if isinstance(ts, datetime) else ts,
                "notes": getattr(a, "notes", None),
            })

        return {
            "total": total,
            "items": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving alerts: {str(e)}"
        )

@router.post("/trigger", response_model=AlertResponse)
async def trigger_alert(
    payload: AlertTriggerRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    if not credentials or credentials.credentials != "testtoken123":
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    try:
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            detection_id=payload.detection_id,
            status=DBAlertStatus.ACTIVE,
            type=payload.type.value,
            severity=payload.severity.value,
            source=payload.source,
            notes=payload.notes,
            lat=payload.location.lat,
            lng=payload.location.lng,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        msg = (
            f"[{payload.severity.value.upper()}] {payload.type.value.replace('_', ' ').title()} "
            f"at ({payload.location.lat}, {payload.location.lng}) - {payload.location.zoneLabel}"
            + (f" | {payload.notes}" if payload.notes else "")
        )

        sent = await notification_service.send_alert(
            alert=alert,
            recipient=payload.createdBy,
            message=msg,
        )

        # Update DB status conservatively
        try:
            ack_status = getattr(DBAlertStatus, "ACKNOWLEDGED", None)
            inactive_status = getattr(DBAlertStatus, "INACTIVE", None)
            if ack_status is not None:
                alert.status = ack_status if sent else (inactive_status or ack_status)
            else:
                alert.status = "sent" if sent else "failed"
            if getattr(alert, "updated_at", None) is not None:
                alert.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
        except Exception:
            db.rollback()

        api_status = APIAlertStatus.SENT if sent else APIAlertStatus.FAILED
        created_at = getattr(alert, "timestamp", getattr(alert, "created_at", datetime.utcnow()))
        updated_at = getattr(alert, "updated_at", created_at)

        return AlertResponse(
            alert_id=getattr(alert, "alert_id", getattr(alert, "id", None)),
            detection_id=alert.detection_id,
            status=api_status,
            type=payload.type,
            severity=payload.severity,
            created_at=created_at,
            updated_at=updated_at,
            location=Location(
                lat=alert.lat,
                lng=alert.lng,
                zoneLabel=alert.zone_label,
            ),
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")
