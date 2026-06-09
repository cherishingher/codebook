from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.utils import public_model
from app.models.attendance import AttendanceRecord
from app.models.course import Course
from app.models.lesson import Lesson, LessonStudent
from app.models.student import Student
from app.models.teacher import Teacher


LESSON_FIELDS = [
    "id",
    "campus_id",
    "course_id",
    "teacher_id",
    "title",
    "classroom_name",
    "start_time",
    "end_time",
    "checkin_start_time",
    "checkin_end_time",
    "late_after_time",
    "default_hour_cost",
    "status",
]


def lesson_summary(lesson: Lesson) -> dict:
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


def lesson_detail(db: Session, lesson: Lesson) -> dict:
    course = db.get(Course, lesson.course_id)
    teacher = db.get(Teacher, lesson.teacher_id)
    rows = db.scalars(
        select(LessonStudent)
        .where(LessonStudent.lesson_id == lesson.id)
        .order_by(LessonStudent.id.asc())
    ).all()

    students = []
    for row in rows:
        student = db.get(Student, row.student_id)
        attendance = db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.lesson_id == lesson.id,
                AttendanceRecord.student_id == row.student_id,
            )
        )
        data = public_model(
            row,
            [
                "id",
                "lesson_id",
                "student_id",
                "planned_hour_cost",
                "attendance_status",
                "deduction_status",
                "deducted_hours",
                "confirmed_by",
                "confirmed_at",
                "note",
            ],
        )
        data["student"] = (
            public_model(student, ["id", "campus_id", "name", "student_no", "phone", "status"])
            if student
            else None
        )
        data["attendance"] = (
            public_model(
                attendance,
                ["id", "attendance_status", "checkin_time", "source", "confirmed_by", "confirmed_at", "note"],
            )
            if attendance
            else None
        )
        students.append(data)

    return {
        "lesson": public_model(lesson, LESSON_FIELDS),
        "course": public_model(course, ["id", "campus_id", "name", "subject", "default_hour_cost", "status"])
        if course
        else None,
        "teacher": public_model(teacher, ["id", "campus_id", "name", "phone", "title", "status"])
        if teacher
        else None,
        "students": students,
    }
