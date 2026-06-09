from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    classroom_name: Mapped[str | None] = mapped_column(String(100))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checkin_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checkin_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    late_after_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    default_hour_cost: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("1.00"))
    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class LessonStudent(TimestampMixin, Base):
    __tablename__ = "lesson_students"
    __table_args__ = (UniqueConstraint("lesson_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    planned_hour_cost: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("1.00"))
    attendance_status: Mapped[str] = mapped_column(String(30), default="pending")
    deduction_status: Mapped[str] = mapped_column(String(30), default="pending")
    deducted_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"))
    confirmed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(String)

