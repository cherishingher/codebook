from datetime import datetime


class LessonService:
    """Lesson creation and punch-to-lesson matching rules."""

    def match_active_lesson(self, *, campus_id: int, student_id: int, captured_at: datetime) -> int | None:
        raise NotImplementedError("Lesson matching query comes next.")

