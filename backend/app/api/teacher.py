from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.utils import public_model
from app.core.database import get_db
from app.models.lesson import Lesson, LessonStudent
from app.schemas.lesson import AttendanceConfirmRequest, LessonCreateRequest
from app.services.attendance_service import AttendanceService

router = APIRouter()


@router.get("/dashboard")
def teacher_dashboard(teacher_id: int, db: Session = Depends(get_db)) -> dict:
    lessons = db.scalars(
        select(Lesson).where(Lesson.teacher_id == teacher_id).order_by(Lesson.start_time.asc()).limit(20)
    ).all()
    return {
        "today_lessons": [
            public_model(
                item,
                ["id", "campus_id", "course_id", "teacher_id", "title", "start_time", "end_time", "status"],
            )
            for item in lessons
        ],
        "pending_confirmations": 0,
    }


@router.get("/lessons")
def teacher_lessons(teacher_id: int, db: Session = Depends(get_db)) -> dict:
    lessons = db.scalars(
        select(Lesson).where(Lesson.teacher_id == teacher_id).order_by(Lesson.start_time.desc())
    ).all()
    return {
        "items": [
            public_model(
                item,
                [
                    "id",
                    "campus_id",
                    "course_id",
                    "teacher_id",
                    "title",
                    "classroom_name",
                    "start_time",
                    "end_time",
                    "status",
                ],
            )
            for item in lessons
        ]
    }


@router.post("/lessons")
def create_lesson(payload: LessonCreateRequest, db: Session = Depends(get_db)) -> dict:
    lesson_data = payload.model_dump(exclude={"student_ids"})
    lesson = Lesson(**lesson_data)
    db.add(lesson)
    db.flush()
    for student_id in payload.student_ids:
        db.add(
            LessonStudent(
                lesson_id=lesson.id,
                student_id=student_id,
                planned_hour_cost=payload.default_hour_cost,
            )
        )
    db.commit()
    db.refresh(lesson)
    return public_model(
        lesson,
        [
            "id",
            "campus_id",
            "course_id",
            "teacher_id",
            "title",
            "classroom_name",
            "start_time",
            "end_time",
            "status",
        ],
    )


@router.post("/lessons/{lesson_id}/attendance/confirm")
def confirm_attendance(
    lesson_id: int,
    payload: AttendanceConfirmRequest,
    db: Session = Depends(get_db),
) -> dict:
    AttendanceService(db).confirm_attendance(
        lesson_id=lesson_id,
        student_id=payload.student_id,
        attendance_status=payload.attendance_status,
        deduction_action=payload.deduction_action,
        operator_user_id=payload.operator_user_id,
        reason=payload.reason,
    )
    db.commit()
    return {"lesson_id": lesson_id, "student_id": payload.student_id, "result": "confirmed"}
