from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord, PunchEvent
from app.models.device import Device
from app.models.lesson import Lesson, LessonStudent
from app.services.hour_service import HourService
from app.services.lesson_service import LessonService


@dataclass(frozen=True)
class PunchProcessResult:
    punch_event_id: int
    matched_lesson_id: int | None
    attendance_status: str
    deduction_status: str
    message: str


class AttendanceService:
    """Coordinates punch events, lesson matching, attendance, and hour deduction."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.lessons = LessonService(db)
        self.hours = HourService(db)

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
        device = self.db.scalar(select(Device).where(Device.device_code == device_code))
        if device is None or device.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found or inactive")

        existing = self.db.scalar(
            select(PunchEvent).where(
                PunchEvent.device_id == device.id,
                PunchEvent.local_event_id == local_event_id,
            )
        )
        if existing:
            return PunchProcessResult(
                punch_event_id=existing.id,
                matched_lesson_id=existing.matched_lesson_id,
                attendance_status="duplicate",
                deduction_status="unchanged",
                message="Duplicate punch event ignored",
            )

        punch = PunchEvent(
            campus_id=device.campus_id,
            device_id=device.id,
            local_event_id=local_event_id,
            student_id=student_id,
            captured_at=captured_at,
            confidence=confidence,
            snapshot_path=snapshot_path,
            raw_payload={
                "device_code": device_code,
                "local_event_id": local_event_id,
                "student_id": student_id,
                "confidence": str(confidence) if confidence is not None else None,
            },
        )
        self.db.add(punch)
        self.db.flush()

        if student_id is None:
            punch.event_type = "unknown"
            punch.process_status = "unknown_face"
            self.db.flush()
            return PunchProcessResult(punch.id, None, "exception", "manual_required", "Unknown face")

        lesson_id = self.lessons.match_active_lesson(
            campus_id=device.campus_id,
            student_id=student_id,
            captured_at=captured_at,
        )
        if lesson_id is None:
            punch.event_type = "arrival"
            punch.process_status = "no_lesson"
            self.db.flush()
            return PunchProcessResult(
                punch.id,
                None,
                "pending",
                "not_deducted",
                "Recorded arrival, no active lesson matched",
            )

        lesson = self.db.get(Lesson, lesson_id)
        if lesson is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

        punch.event_type = "lesson_checkin"
        punch.matched_lesson_id = lesson.id
        attendance_status = "present" if captured_at <= lesson.late_after_time else "late"

        existing_attendance = self.db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.lesson_id == lesson.id,
                AttendanceRecord.student_id == student_id,
            )
        )
        if existing_attendance:
            punch.process_status = "duplicate_attendance"
            self.db.flush()
            lesson_student = self._get_lesson_student(lesson.id, student_id)
            return PunchProcessResult(
                punch.id,
                lesson.id,
                existing_attendance.attendance_status,
                lesson_student.deduction_status if lesson_student else "unchanged",
                "Attendance already exists for this lesson",
            )

        attendance = AttendanceRecord(
            campus_id=device.campus_id,
            lesson_id=lesson.id,
            student_id=student_id,
            punch_event_id=punch.id,
            attendance_status=attendance_status,
            checkin_time=captured_at,
            source="face_auto",
        )
        self.db.add(attendance)
        self.db.flush()

        lesson_student = self._get_lesson_student(lesson.id, student_id)
        if lesson_student:
            lesson_student.attendance_status = attendance_status
            lesson_student.confirmed_at = captured_at

        deduction_status = self._apply_rule(lesson, attendance, operator_user_id=None)
        punch.process_status = "matched"
        self.db.flush()
        return PunchProcessResult(
            punch.id,
            lesson.id,
            attendance_status,
            deduction_status,
            "Lesson attendance processed",
        )

    def confirm_attendance(
        self,
        *,
        lesson_id: int,
        student_id: int,
        attendance_status: str,
        deduction_action: str,
        operator_user_id: int | None,
        reason: str,
    ) -> None:
        lesson = self.db.get(Lesson, lesson_id)
        if lesson is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

        lesson_student = self._get_lesson_student(lesson_id, student_id)
        if lesson_student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not in this lesson")

        attendance = self.db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.lesson_id == lesson_id,
                AttendanceRecord.student_id == student_id,
            )
        )
        if attendance is None:
            attendance = AttendanceRecord(
                campus_id=lesson.campus_id,
                lesson_id=lesson_id,
                student_id=student_id,
                attendance_status=attendance_status,
                source="teacher_manual",
                confirmed_by=operator_user_id,
                confirmed_at=datetime.now(),
                note=reason,
            )
            self.db.add(attendance)
            self.db.flush()
        else:
            attendance.attendance_status = attendance_status
            attendance.source = "teacher_manual"
            attendance.confirmed_by = operator_user_id
            attendance.confirmed_at = datetime.now()
            attendance.note = reason

        lesson_student.attendance_status = attendance_status
        lesson_student.confirmed_by = operator_user_id
        lesson_student.confirmed_at = datetime.now()
        lesson_student.note = reason

        if deduction_action == "deduct":
            self.hours.apply_deduction(
                attendance_record_id=attendance.id,
                operator_user_id=operator_user_id,
                source="teacher_manual",
                reason=reason,
            )
            lesson_student.deduction_status = "deducted"
            lesson_student.deducted_hours = lesson.default_hour_cost
        elif deduction_action == "not_deduct":
            self._restore_deduction_if_exists(
                attendance_record_id=attendance.id,
                operator_user_id=operator_user_id,
                reason=reason,
            )
            lesson_student.deduction_status = "not_deducted"
            lesson_student.deducted_hours = Decimal("0.00")
        elif deduction_action == "manual_required":
            self._restore_deduction_if_exists(
                attendance_record_id=attendance.id,
                operator_user_id=operator_user_id,
                reason=reason,
            )
            lesson_student.deduction_status = "manual_required"
            lesson_student.deducted_hours = Decimal("0.00")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid deduction action")

        self.db.flush()

    def _apply_rule(
        self,
        lesson: Lesson,
        attendance: AttendanceRecord,
        operator_user_id: int | None,
    ) -> str:
        action = self.hours.resolve_deduction_action(
            lesson=lesson,
            attendance_status=attendance.attendance_status,
        )
        lesson_student = self._get_lesson_student(lesson.id, attendance.student_id)
        if action == "deduct":
            try:
                self.hours.apply_deduction(
                    attendance_record_id=attendance.id,
                    operator_user_id=operator_user_id,
                    source="face_auto",
                    reason="Face attendance auto deduction",
                )
            except HTTPException as exc:
                if exc.status_code == status.HTTP_409_CONFLICT and lesson_student:
                    lesson_student.deduction_status = "manual_required"
                    return "manual_required"
                raise
            if lesson_student:
                lesson_student.deduction_status = "deducted"
                lesson_student.deducted_hours = lesson.default_hour_cost
            return "deducted"
        if action == "not_deduct":
            if lesson_student:
                lesson_student.deduction_status = "not_deducted"
                lesson_student.deducted_hours = Decimal("0.00")
            return "not_deducted"
        if lesson_student:
            lesson_student.deduction_status = "manual_required"
        return "manual_required"

    def _get_lesson_student(self, lesson_id: int, student_id: int) -> LessonStudent | None:
        return self.db.scalar(
            select(LessonStudent).where(
                LessonStudent.lesson_id == lesson_id,
                LessonStudent.student_id == student_id,
            )
        )

    def _restore_deduction_if_exists(
        self,
        *,
        attendance_record_id: int,
        operator_user_id: int | None,
        reason: str,
    ) -> None:
        try:
            self.hours.restore_deduction(
                attendance_record_id=attendance_record_id,
                operator_user_id=operator_user_id,
                reason=reason,
            )
        except HTTPException as exc:
            if exc.status_code != status.HTTP_404_NOT_FOUND:
                raise
