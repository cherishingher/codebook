from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class LessonCreateRequest(BaseModel):
    course_id: int
    title: str
    classroom_name: str | None = None
    start_time: datetime
    end_time: datetime
    checkin_start_time: datetime
    checkin_end_time: datetime
    late_after_time: datetime
    default_hour_cost: Decimal = Field(default=Decimal("1.00"), ge=0)
    student_ids: list[int]


class AttendanceConfirmRequest(BaseModel):
    student_id: int
    attendance_status: str
    deduction_action: str
    deducted_hours: Decimal = Field(default=Decimal("0.00"), ge=0)
    reason: str

