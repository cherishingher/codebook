from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson import Lesson, LessonStudent


class LessonService:
    """Lesson creation and punch-to-lesson matching rules."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def match_active_lesson(self, *, campus_id: int, student_id: int, captured_at: datetime) -> int | None:
        candidates = self.db.scalars(
            select(Lesson)
            .join(LessonStudent, LessonStudent.lesson_id == Lesson.id)
            .where(
                Lesson.campus_id == campus_id,
                LessonStudent.student_id == student_id,
                Lesson.status != "cancelled",
                Lesson.checkin_start_time <= captured_at,
                Lesson.checkin_end_time >= captured_at,
            )
            .order_by(Lesson.start_time.asc())
        ).all()
        if len(candidates) != 1:
            return None
        return candidates[0].id
