from fastapi import APIRouter

from app.schemas.lesson import AttendanceConfirmRequest, LessonCreateRequest

router = APIRouter()


@router.get("/dashboard")
def teacher_dashboard() -> dict:
    return {"today_lessons": [], "pending_confirmations": 0}


@router.post("/lessons")
def create_lesson(payload: LessonCreateRequest) -> dict:
    return {"id": 0, "status": "scheduled", "payload": payload.model_dump()}


@router.post("/lessons/{lesson_id}/attendance/confirm")
def confirm_attendance(lesson_id: int, payload: AttendanceConfirmRequest) -> dict:
    return {"lesson_id": lesson_id, "result": "accepted", "payload": payload.model_dump()}

