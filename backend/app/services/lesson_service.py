from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson, LessonStudent
from app.models.student import Student
from app.models.teacher import Teacher


class LessonService:
    """Lesson creation and punch-to-lesson matching rules."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_lesson(
        self,
        *,
        campus_id: int,
        course_id: int,
        teacher_id: int,
        title: str,
        classroom_name: str | None,
        start_time: datetime,
        end_time: datetime,
        checkin_start_time: datetime,
        checkin_end_time: datetime,
        late_after_time: datetime,
        default_hour_cost: Decimal,
        student_ids: list[int],
    ) -> Lesson:
        self._validate_lesson_time_window(
            start_time=start_time,
            end_time=end_time,
            checkin_start_time=checkin_start_time,
            checkin_end_time=checkin_end_time,
            late_after_time=late_after_time,
        )
        normalized_student_ids = self._validate_student_ids(student_ids)
        course = self.db.get(Course, course_id)
        if course is None or course.campus_id != campus_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course is not in this campus")

        teacher = self.db.get(Teacher, teacher_id)
        if teacher is None or teacher.campus_id != campus_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher is not in this campus")

        students = self.db.scalars(
            select(Student).where(Student.id.in_(normalized_student_ids), Student.campus_id == campus_id)
        ).all()
        if len(students) != len(normalized_student_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Some students are not in this campus")

        lesson = Lesson(
            campus_id=campus_id,
            course_id=course_id,
            teacher_id=teacher_id,
            title=title,
            classroom_name=classroom_name,
            start_time=start_time,
            end_time=end_time,
            checkin_start_time=checkin_start_time,
            checkin_end_time=checkin_end_time,
            late_after_time=late_after_time,
            default_hour_cost=default_hour_cost,
        )
        self.db.add(lesson)
        self.db.flush()
        for student_id in normalized_student_ids:
            self.db.add(
                LessonStudent(
                    lesson_id=lesson.id,
                    student_id=student_id,
                    planned_hour_cost=default_hour_cost,
                )
            )
        self.db.flush()
        return lesson

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

    @staticmethod
    def _validate_student_ids(student_ids: list[int]) -> list[int]:
        normalized = list(dict.fromkeys(student_ids))
        if not normalized:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one student is required")
        if len(normalized) != len(student_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate student ids are not allowed")
        return normalized

    @staticmethod
    def _validate_lesson_time_window(
        *,
        start_time: datetime,
        end_time: datetime,
        checkin_start_time: datetime,
        checkin_end_time: datetime,
        late_after_time: datetime,
    ) -> None:
        if end_time <= start_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lesson end time must be after start")
        if checkin_end_time <= checkin_start_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Check-in end time must be after start")
        if not checkin_start_time <= late_after_time <= checkin_end_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Late time must be inside check-in window")
