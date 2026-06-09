from decimal import Decimal

from pydantic import BaseModel, Field


class HourAccountCreate(BaseModel):
    campus_id: int
    student_id: int
    course_id: int
    initial_hours: Decimal = Field(default=Decimal("0.00"))
    reason: str = "Initial balance"


class HourLedgerCreate(BaseModel):
    change_type: str
    change_hours: Decimal
    reason: str
    operator_user_id: int | None = None


class DeductionRuleUpsert(BaseModel):
    campus_id: int
    scope_type: str = "campus"
    scope_id: int | None = None
    present_action: str = "deduct"
    late_action: str = "deduct"
    absent_action: str = "manual_required"
    leave_action: str = "not_deduct"
    exception_action: str = "manual_required"

