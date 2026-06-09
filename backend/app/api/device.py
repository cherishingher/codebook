from fastapi import APIRouter

from app.schemas.device import DeviceHeartbeatRequest, PunchEventRequest

router = APIRouter()


@router.post("/heartbeat")
def heartbeat(payload: DeviceHeartbeatRequest) -> dict:
    return {"device_code": payload.device_code, "status": "ok"}


@router.post("/punch-events")
def punch_event(payload: PunchEventRequest) -> dict:
    return {
        "punch_event_id": 0,
        "matched_lesson_id": None,
        "attendance_status": "pending",
        "deduction_status": "pending",
        "message": "Punch event accepted",
        "payload": payload.model_dump(),
    }


@router.get("/face-profiles")
def face_profiles(device_code: str, updated_after: str | None = None) -> dict:
    return {"device_code": device_code, "updated_after": updated_after, "items": []}

