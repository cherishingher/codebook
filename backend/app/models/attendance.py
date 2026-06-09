from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class PunchEvent(Base):
    __tablename__ = "punch_events"
    __table_args__ = (UniqueConstraint("device_id", "local_event_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, index=True)
    local_event_id: Mapped[str] = mapped_column(String(100), nullable=False)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    snapshot_path: Mapped[str | None] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String(30), default="unknown")
    matched_lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"))
    process_status: Mapped[str] = mapped_column(String(30), default="unprocessed")
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AttendanceRecord(TimestampMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("lesson_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False, index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    punch_event_id: Mapped[int | None] = mapped_column(ForeignKey("punch_events.id"))
    attendance_status: Mapped[str] = mapped_column(String(30), default="pending")
    checkin_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(30), default="system")
    confirmed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(String)
