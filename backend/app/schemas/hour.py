from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class HourAccountCreate(BaseModel):
    campus_id: int
    student_id: int
    course_id: int
    initial_hours: Decimal = Field(default=Decimal("0.00"))
    reason: str = "Initial balance"


class HourLedgerCreate(BaseModel):
    change_type: Literal["add", "deduct", "refund", "adjust", "restore", "void"]
    change_hours: Decimal
    reason: str
    operator_user_id: int | None = None


class DeductionRuleUpsert(BaseModel):
    campus_id: int
    scope_type: Literal["campus", "course", "lesson", "teacher"] = "campus"
    scope_id: int | None = None
    present_action: Literal["deduct", "not_deduct", "manual_required"] = "deduct"
    late_action: Literal["deduct", "not_deduct", "manual_required"] = "deduct"
    absent_action: Literal["deduct", "not_deduct", "manual_required"] = "manual_required"
    leave_action: Literal["deduct", "not_deduct", "manual_required"] = "not_deduct"
    exception_action: Literal["deduct", "not_deduct", "manual_required"] = "manual_required"
