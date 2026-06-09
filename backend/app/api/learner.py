from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.utils import public_model
from app.core.database import get_db
from app.models.attendance import AttendanceRecord
from app.models.course import Course
from app.models.hour import HourAccount, HourLedger
from app.models.lesson import Lesson, LessonStudent
from app.models.student import Student

router = APIRouter()


@router.get("/dashboard")
def learner_dashboard(student_id: int, db: Session = Depends(get_db)) -> dict:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    lessons = db.scalars(
        select(Lesson)
        .join(LessonStudent, LessonStudent.lesson_id == Lesson.id)
        .where(LessonStudent.student_id == student_id)
        .order_by(Lesson.start_time.asc())
        .limit(10)
    ).all()
    accounts = db.scalars(select(HourAccount).where(HourAccount.student_id == student_id)).all()
    return {
        "student": {"id": student_id, "name": student.name if student else ""},
        "today_lessons": [
            public_model(
                item,
                ["id", "campus_id", "course_id", "teacher_id", "title", "start_time", "end_time", "status"],
            )
            for item in lessons
        ],
        "hour_summary": [
            public_model(account, ["id", "course_id", "balance_hours", "status"]) for account in accounts
        ],
    }


@router.get("/lessons")
def learner_lessons(
    student_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    query = (
        select(Lesson)
        .join(LessonStudent, LessonStudent.lesson_id == Lesson.id)
        .where(LessonStudent.student_id == student_id)
    )
    if start_date:
        query = query.where(Lesson.start_time >= _parse_date_boundary(start_date, start=True))
    if end_date:
        query = query.where(Lesson.start_time <= _parse_date_boundary(end_date, start=False))
    lessons = db.scalars(query.order_by(Lesson.start_time.asc())).all()
    return {
        "student_id": student_id,
        "start_date": start_date,
        "end_date": end_date,
        "items": [
            public_model(
                item,
                ["id", "campus_id", "course_id", "teacher_id", "title", "start_time", "end_time", "status"],
            )
            for item in lessons
        ],
    }


@router.get("/lessons/{lesson_id}")
def learner_lesson_detail(lesson_id: int, student_id: int, db: Session = Depends(get_db)) -> dict:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    lesson_student = db.scalar(
        select(LessonStudent).where(
            LessonStudent.lesson_id == lesson_id,
            LessonStudent.student_id == student_id,
        )
    )
    if lesson_student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not in this lesson")
    attendance = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.lesson_id == lesson_id,
            AttendanceRecord.student_id == student_id,
        )
    )
    return {
        "lesson": public_model(
            lesson,
            ["id", "campus_id", "course_id", "teacher_id", "title", "start_time", "end_time", "status"],
        ),
        "lesson_student": public_model(
            lesson_student,
            [
                "id",
                "lesson_id",
                "student_id",
                "planned_hour_cost",
                "attendance_status",
                "deduction_status",
                "deducted_hours",
                "note",
            ],
        ),
        "attendance": public_model(
            attendance,
            ["id", "attendance_status", "checkin_time", "source", "confirmed_by", "confirmed_at", "note"],
        )
        if attendance
        else None,
    }


def _parse_date_boundary(value: str, *, start: bool) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format") from exc
    if parsed.time() == time.min:
        return datetime.combine(parsed.date(), time.min if start else time.max)
    return parsed


@router.get("/hour-accounts")
def learner_hour_accounts(student_id: int, db: Session = Depends(get_db)) -> dict:
    accounts = db.scalars(select(HourAccount).where(HourAccount.student_id == student_id)).all()
    items = []
    for account in accounts:
        course = db.get(Course, account.course_id)
        data = public_model(account, ["id", "campus_id", "student_id", "course_id", "balance_hours", "status"])
        data["course_name"] = course.name if course else ""
        items.append(data)
    return {"items": items}


@router.get("/hour-ledgers")
def learner_hour_ledgers(
    student_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    items = db.scalars(
        select(HourLedger)
        .where(HourLedger.student_id == student_id)
        .order_by(HourLedger.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "student_id": student_id,
        "page": page,
        "page_size": page_size,
        "items": [
            public_model(
                item,
                [
                    "id",
                    "course_id",
                    "lesson_id",
                    "change_type",
                    "change_hours",
                    "balance_before",
                    "balance_after",
                    "source",
                    "reason",
                    "created_at",
                ],
            )
            for item in items
        ],
    }
