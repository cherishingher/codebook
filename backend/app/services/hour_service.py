from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord
from app.models.hour import DeductionRule, HourAccount, HourLedger
from app.models.lesson import Lesson


@dataclass(frozen=True)
class LedgerResult:
    ledger_id: int | None
    balance_before: Decimal
    balance_after: Decimal


class HourService:
    """Single entrypoint for all hour balance changes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_account(
        self,
        *,
        campus_id: int,
        student_id: int,
        course_id: int,
        initial_hours: Decimal,
        operator_user_id: int | None,
        reason: str,
    ) -> HourAccount:
        existing = self.db.scalar(
            select(HourAccount).where(
                HourAccount.student_id == student_id,
                HourAccount.course_id == course_id,
            )
        )
        if existing:
            if initial_hours != Decimal("0.00"):
                self.create_ledger(
                    account_id=existing.id,
                    change_type="add",
                    change_hours=initial_hours,
                    operator_user_id=operator_user_id,
                    source="campus_manual",
                    reason=reason,
                )
            return existing

        account = HourAccount(
            campus_id=campus_id,
            student_id=student_id,
            course_id=course_id,
            balance_hours=Decimal("0.00"),
        )
        self.db.add(account)
        self.db.flush()
        if initial_hours != Decimal("0.00"):
            self.create_ledger(
                account_id=account.id,
                change_type="add",
                change_hours=initial_hours,
                operator_user_id=operator_user_id,
                source="campus_manual",
                reason=reason,
            )
        return account

    def create_ledger(
        self,
        *,
        account_id: int,
        change_type: str,
        change_hours: Decimal,
        operator_user_id: int | None,
        source: str = "system",
        reason: str,
        lesson_id: int | None = None,
        attendance_record_id: int | None = None,
        related_ledger_id: int | None = None,
    ) -> LedgerResult:
        account = self.db.scalar(
            select(HourAccount).where(HourAccount.id == account_id).with_for_update()
        )
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hour account not found")

        normalized_change = self._normalize_change(change_type, change_hours)
        if attendance_record_id and change_type == "deduct":
            existing = self._active_deduction(attendance_record_id)
            if existing:
                return LedgerResult(existing.id, existing.balance_before, existing.balance_after)

        balance_before = Decimal(account.balance_hours)
        balance_after = balance_before + normalized_change
        account.balance_hours = balance_after
        ledger_source = self._unique_source(
            attendance_record_id=attendance_record_id,
            change_type=change_type,
            source=source,
        )

        ledger = HourLedger(
            campus_id=account.campus_id,
            account_id=account.id,
            student_id=account.student_id,
            course_id=account.course_id,
            lesson_id=lesson_id,
            attendance_record_id=attendance_record_id,
            change_type=change_type,
            change_hours=normalized_change,
            balance_before=balance_before,
            balance_after=balance_after,
            operator_user_id=operator_user_id,
            source=ledger_source,
            reason=reason,
            related_ledger_id=related_ledger_id,
        )
        self.db.add(ledger)
        self.db.flush()
        return LedgerResult(ledger.id, balance_before, balance_after)

    def apply_deduction(
        self,
        *,
        attendance_record_id: int,
        operator_user_id: int | None,
        source: str = "system",
        reason: str = "Attendance deduction",
    ) -> LedgerResult:
        attendance = self.db.get(AttendanceRecord, attendance_record_id)
        if attendance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance not found")

        lesson = self.db.get(Lesson, attendance.lesson_id)
        if lesson is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

        account = self.db.scalar(
            select(HourAccount).where(
                HourAccount.student_id == attendance.student_id,
                HourAccount.course_id == lesson.course_id,
            )
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Hour account not found for this course",
            )

        return self.create_ledger(
            account_id=account.id,
            change_type="deduct",
            change_hours=lesson.default_hour_cost,
            operator_user_id=operator_user_id,
            source=source,
            reason=reason,
            lesson_id=lesson.id,
            attendance_record_id=attendance.id,
        )

    def restore_deduction(
        self,
        *,
        attendance_record_id: int,
        operator_user_id: int | None,
        reason: str,
    ) -> LedgerResult:
        original = self.db.scalar(
            select(HourLedger).where(
                HourLedger.attendance_record_id == attendance_record_id,
                HourLedger.change_type == "deduct",
            )
        )
        if original is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deduction ledger not found")

        existing_restore = self.db.scalar(
            select(HourLedger).where(
                HourLedger.related_ledger_id == original.id,
                HourLedger.change_type == "restore",
            )
        )
        if existing_restore:
            return LedgerResult(
                existing_restore.id,
                existing_restore.balance_before,
                existing_restore.balance_after,
            )

        return self.create_ledger(
            account_id=original.account_id,
            change_type="restore",
            change_hours=abs(Decimal(original.change_hours)),
            operator_user_id=operator_user_id,
            source="manual_correction",
            reason=reason,
            lesson_id=original.lesson_id,
            attendance_record_id=attendance_record_id,
            related_ledger_id=original.id,
        )

    def resolve_deduction_action(self, *, lesson: Lesson, attendance_status: str) -> str:
        rules = [
            self.db.scalar(
                select(DeductionRule).where(
                    DeductionRule.campus_id == lesson.campus_id,
                    DeductionRule.scope_type == "lesson",
                    DeductionRule.scope_id == lesson.id,
                )
            ),
            self.db.scalar(
                select(DeductionRule).where(
                    DeductionRule.campus_id == lesson.campus_id,
                    DeductionRule.scope_type == "course",
                    DeductionRule.scope_id == lesson.course_id,
                )
            ),
            self.db.scalar(
                select(DeductionRule).where(
                    DeductionRule.campus_id == lesson.campus_id,
                    DeductionRule.scope_type == "teacher",
                    DeductionRule.scope_id == lesson.teacher_id,
                )
            ),
            self.db.scalar(
                select(DeductionRule).where(
                    DeductionRule.campus_id == lesson.campus_id,
                    DeductionRule.scope_type == "campus",
                    DeductionRule.scope_id.is_(None),
                )
            ),
        ]
        rule = next((item for item in rules if item is not None), None)
        if rule is None:
            defaults = {
                "present": "deduct",
                "late": "deduct",
                "absent": "manual_required",
                "leave": "not_deduct",
                "exception": "manual_required",
            }
            return defaults.get(attendance_status, "manual_required")
        return getattr(rule, f"{attendance_status}_action", "manual_required")

    @staticmethod
    def _normalize_change(change_type: str, change_hours: Decimal) -> Decimal:
        amount = abs(Decimal(change_hours))
        if change_type == "deduct":
            return -amount
        if change_type in {"add", "refund", "adjust", "restore"}:
            return amount
        if change_type == "void":
            return -amount
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported ledger type")

    def _active_deduction(self, attendance_record_id: int) -> HourLedger | None:
        deductions = self.db.scalars(
            select(HourLedger)
            .where(
                HourLedger.attendance_record_id == attendance_record_id,
                HourLedger.change_type == "deduct",
            )
            .order_by(HourLedger.id.desc())
        ).all()
        for deduction in deductions:
            restored = self.db.scalar(
                select(HourLedger).where(
                    HourLedger.related_ledger_id == deduction.id,
                    HourLedger.change_type == "restore",
                )
            )
            if restored is None:
                return deduction
        return None

    def _unique_source(self, *, attendance_record_id: int | None, change_type: str, source: str) -> str:
        if attendance_record_id is None:
            return source
        candidate = source
        suffix = 2
        while self.db.scalar(
            select(HourLedger.id).where(
                HourLedger.attendance_record_id == attendance_record_id,
                HourLedger.change_type == change_type,
                HourLedger.source == candidate,
            )
        ):
            candidate = f"{source}_{suffix}"
            suffix += 1
        return candidate
