from datetime import datetime
import base64

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device
from app.models.face import FaceProfile
from app.schemas.device import DeviceHeartbeatRequest, PunchEventRequest
from app.services.attendance_service import AttendanceService

router = APIRouter()


@router.post("/heartbeat")
def heartbeat(payload: DeviceHeartbeatRequest, db: Session = Depends(get_db)) -> dict:
    device = db.scalar(select(Device).where(Device.device_code == payload.device_code))
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    device.last_seen_at = datetime.now()
    device.status = "active"
    db.commit()
    return {"device_code": payload.device_code, "status": "ok"}


@router.post("/punch-events")
def punch_event(payload: PunchEventRequest, db: Session = Depends(get_db)) -> dict:
    result = AttendanceService(db).process_punch_event(
        device_code=payload.device_code,
        local_event_id=payload.local_event_id,
        student_id=payload.student_id,
        captured_at=payload.captured_at,
        confidence=payload.confidence,
        snapshot_path=payload.snapshot_path,
    )
    db.commit()
    return {
        "punch_event_id": result.punch_event_id,
        "matched_lesson_id": result.matched_lesson_id,
        "attendance_status": result.attendance_status,
        "deduction_status": result.deduction_status,
        "message": result.message,
    }


@router.get("/face-profiles")
def face_profiles(device_code: str, updated_after: str | None = None, db: Session = Depends(get_db)) -> dict:
    device = db.scalar(select(Device).where(Device.device_code == device_code))
    if device is None or device.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found or inactive")
    query = select(FaceProfile).where(
        FaceProfile.campus_id == device.campus_id,
        FaceProfile.status == "active",
        FaceProfile.consent_status == "granted",
    )
    if updated_after:
        query = query.where(FaceProfile.updated_at >= datetime.fromisoformat(updated_after))
    items = db.scalars(query.order_by(FaceProfile.updated_at.asc())).all()
    return {
        "device_code": device_code,
        "updated_after": updated_after,
        "items": [
            {
                "id": item.id,
                "student_id": item.student_id,
                "feature_version": item.feature_version,
                "feature_data": base64.b64encode(item.feature_data).decode("ascii"),
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            for item in items
        ],
    }
