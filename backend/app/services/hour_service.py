from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LedgerResult:
    ledger_id: int | None
    balance_before: Decimal
    balance_after: Decimal


class HourService:
    """Single entrypoint for all hour balance changes."""

    def create_ledger(
        self,
        *,
        account_id: int,
        change_type: str,
        change_hours: Decimal,
        operator_user_id: int | None,
        reason: str,
    ) -> LedgerResult:
        raise NotImplementedError("Database transaction implementation comes next.")

    def apply_deduction(
        self,
        *,
        attendance_record_id: int,
        planned_hours: Decimal,
        operator_user_id: int | None,
    ) -> LedgerResult:
        raise NotImplementedError("Deduction transaction implementation comes next.")

