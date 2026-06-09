import base64
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_device_signature
from app.models.device import Device, DeviceNonce
from app.models.face import FaceProfile
from app.schemas.device import DeviceHeartbeatRequest, PunchEventRequest
from app.services.attendance_service import AttendanceService

router = APIRouter()


async def verify_device_request(
    request: Request,
    x_device_code: str | None = Header(default=None, alias="X-Codebook-Device-Code"),
    x_timestamp: str | None = Header(default=None, alias="X-Codebook-Timestamp"),
    x_nonce: str | None = Header(default=None, alias="X-Codebook-Nonce"),
    x_signature: str | None = Header(default=None, alias="X-Codebook-Signature"),
    db: Session = Depends(get_db),
) -> Device:
    if not all([x_device_code, x_timestamp, x_nonce, x_signature]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing device signature headers")

    device = db.scalar(select(Device).where(Device.device_code == x_device_code))
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if device.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device is inactive")

    signed_at = _parse_signed_at(x_timestamp)
    age_seconds = abs((datetime.now(UTC) - signed_at).total_seconds())
    if age_seconds > settings.device_signature_tolerance_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired device signature")

    body = await request.body()
    if not verify_device_signature(device.secret_hash, x_timestamp, x_nonce, body, x_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device signature")

    _prune_expired_nonces(db, device.id)
    existing_nonce = db.scalar(
        select(DeviceNonce).where(DeviceNonce.device_id == device.id, DeviceNonce.nonce == x_nonce)
    )
    if existing_nonce is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device signature nonce was already used")

    db.add(DeviceNonce(device_id=device.id, nonce=x_nonce, timestamp=signed_at))
    db.flush()
    return device


@router.post("/heartbeat")
def heartbeat(
    payload: DeviceHeartbeatRequest,
    device: Device = Depends(verify_device_request),
    db: Session = Depends(get_db),
) -> dict:
    _assert_payload_device(payload.device_code, device)
    device.last_seen_at = datetime.now(UTC)
    device.status = "active"
    db.commit()
    return {"device_code": payload.device_code, "status": "ok"}


@router.post("/punch-events")
def punch_event(
    payload: PunchEventRequest,
    device: Device = Depends(verify_device_request),
    db: Session = Depends(get_db),
) -> dict:
    _assert_payload_device(payload.device_code, device)
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
def face_profiles(
    device_code: str,
    updated_after: str | None = None,
    device: Device = Depends(verify_device_request),
    db: Session = Depends(get_db),
) -> dict:
    _assert_payload_device(device_code, device)
    query = select(FaceProfile).where(
        FaceProfile.campus_id == device.campus_id,
        FaceProfile.status == "active",
        FaceProfile.consent_status == "granted",
    )
    if updated_after:
        query = query.where(FaceProfile.updated_at >= datetime.fromisoformat(updated_after))
    items = db.scalars(query.order_by(FaceProfile.updated_at.asc())).all()
    db.commit()
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


def _parse_signed_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device timestamp") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _assert_payload_device(device_code: str, device: Device) -> None:
    if device_code != device.device_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device code does not match signature")


def _prune_expired_nonces(db: Session, device_id: int) -> None:
    cutoff = datetime.now(UTC) - timedelta(seconds=settings.device_signature_tolerance_seconds * 2)
    db.execute(delete(DeviceNonce).where(DeviceNonce.device_id == device_id, DeviceNonce.created_at < cutoff))
