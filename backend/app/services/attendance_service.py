from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class PunchProcessResult:
    punch_event_id: int
    matched_lesson_id: int | None
    attendance_status: str
    deduction_status: str
    message: str


class AttendanceService:
    """Coordinates punch events, lesson matching, attendance, and hour deduction."""

    def process_punch_event(
        self,
        *,
        device_code: str,
        local_event_id: str,
        student_id: int | None,
        captured_at: datetime,
        confidence: Decimal | None,
        snapshot_path: str | None,
    ) -> PunchProcessResult:
        raise NotImplementedError("Idempotent punch handling comes next.")

    def confirm_attendance(
        self,
        *,
        lesson_id: int,
        student_id: int,
        attendance_status: str,
        deduction_action: str,
        operator_user_id: int,
        reason: str,
    ) -> None:
        raise NotImplementedError("Manual confirmation transaction comes next.")

