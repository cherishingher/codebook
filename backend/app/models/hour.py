from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class HourAccount(TimestampMixin, Base):
    __tablename__ = "hour_accounts"
    __table_args__ = (UniqueConstraint("student_id", "course_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    balance_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(20), default="active")


class HourLedger(Base):
    __tablename__ = "hour_ledgers"

    id: Mapped[int] = mapped_column(primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("hour_accounts.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"))
    attendance_record_id: Mapped[int | None] = mapped_column(ForeignKey("attendance_records.id"))
    change_type: Mapped[str] = mapped_column(String(30), nullable=False)
    change_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    operator_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    source: Mapped[str] = mapped_column(String(30), default="system")
    reason: Mapped[str | None] = mapped_column(String)
    related_ledger_id: Mapped[int | None] = mapped_column(ForeignKey("hour_ledgers.id"))


class DeductionRule(TimestampMixin, Base):
    __tablename__ = "deduction_rules"
    __table_args__ = (UniqueConstraint("campus_id", "scope_type", "scope_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False, index=True)
    scope_type: Mapped[str] = mapped_column(String(30), default="campus")
    scope_id: Mapped[int | None] = mapped_column()
    present_action: Mapped[str] = mapped_column(String(30), default="deduct")
    late_action: Mapped[str] = mapped_column(String(30), default="deduct")
    absent_action: Mapped[str] = mapped_column(String(30), default="manual_required")
    leave_action: Mapped[str] = mapped_column(String(30), default="not_deduct")
    exception_action: Mapped[str] = mapped_column(String(30), default="manual_required")

