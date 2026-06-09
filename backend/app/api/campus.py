from decimal import Decimal
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.utils import page_response, public_model
from app.core.database import get_db
from app.models.attendance import AttendanceRecord
from app.models.campus import Campus
from app.models.course import Course
from app.models.device import Device
from app.models.hour import DeductionRule, HourAccount, HourLedger
from app.models.lesson import Lesson, LessonStudent
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.campus import CampusCreate, CourseCreate, DeviceCreate, StudentCreate, TeacherCreate
from app.schemas.hour import DeductionRuleUpsert, HourAccountCreate, HourLedgerCreate
from app.schemas.lesson import LessonCreateRequest
from app.services.hour_service import HourService

router = APIRouter()


@router.get("/dashboard")
def campus_dashboard(campus_id: int, db: Session = Depends(get_db)) -> dict:
    lessons_today = db.scalar(select(func.count(Lesson.id)).where(Lesson.campus_id == campus_id)) or 0
    expected = (
        db.scalar(
            select(func.count(LessonStudent.id))
            .join(Lesson, Lesson.id == LessonStudent.lesson_id)
            .where(Lesson.campus_id == campus_id)
        )
        or 0
    )
    present = (
        db.scalar(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.campus_id == campus_id,
                AttendanceRecord.attendance_status.in_(["present", "late"]),
            )
        )
        or 0
    )
    late = (
        db.scalar(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.campus_id == campus_id,
                AttendanceRecord.attendance_status == "late",
            )
        )
        or 0
    )
    absent = (
        db.scalar(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.campus_id == campus_id,
                AttendanceRecord.attendance_status == "absent",
            )
        )
        or 0
    )
    deducted = (
        db.scalar(
            select(func.coalesce(func.sum(HourLedger.change_hours), 0)).where(
                HourLedger.campus_id == campus_id,
                HourLedger.change_type == "deduct",
            )
        )
        or Decimal("0.00")
    )
    devices_online = (
        db.scalar(
            select(func.count(Device.id)).where(Device.campus_id == campus_id, Device.status == "active")
        )
        or 0
    )
    return {
        "today_lessons": lessons_today,
        "expected_attendances": expected,
        "present_count": present,
        "late_count": late,
        "absent_count": absent,
        "deducted_hours": abs(float(deducted)),
        "pending_exceptions": 0,
        "devices_online": devices_online,
    }


@router.post("/campuses")
def create_campus(payload: CampusCreate, db: Session = Depends(get_db)) -> dict:
    campus = Campus(**payload.model_dump())
    db.add(campus)
    db.commit()
    db.refresh(campus)
    return public_model(campus, ["id", "name", "code", "address", "contact_name", "contact_phone", "status"])


@router.get("/campuses")
def campuses(db: Session = Depends(get_db)) -> dict:
    items = db.scalars(select(Campus).order_by(Campus.id.asc())).all()
    return {"items": [public_model(item, ["id", "name", "code", "status"]) for item in items]}


@router.get("/students")
def students(
    campus_id: int | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    query = select(Student)
    if campus_id is not None:
        query = query.where(Student.campus_id == campus_id)
    if keyword:
        query = query.where(Student.name.contains(keyword))
    rows = db.scalars(query.order_by(Student.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return page_response(
        [public_model(item, ["id", "campus_id", "name", "student_no", "gender", "phone", "status"]) for item in rows],
        page=page,
        page_size=page_size,
    )


@router.post("/students")
def create_student(payload: StudentCreate, db: Session = Depends(get_db)) -> dict:
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return public_model(student, ["id", "campus_id", "name", "student_no", "gender", "phone", "status"])


@router.get("/students/{student_id}")
def student_detail(student_id: int, db: Session = Depends(get_db)) -> dict:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    accounts = db.scalars(select(HourAccount).where(HourAccount.student_id == student_id)).all()
    return {
        "student": public_model(student, ["id", "campus_id", "name", "student_no", "gender", "phone", "status"]),
        "hour_accounts": [
            public_model(account, ["id", "campus_id", "student_id", "course_id", "balance_hours", "status"])
            for account in accounts
        ],
    }


@router.post("/teachers")
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_db)) -> dict:
    teacher = Teacher(**payload.model_dump())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return public_model(teacher, ["id", "campus_id", "name", "phone", "title", "status"])


@router.get("/teachers")
def teachers(campus_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    query = select(Teacher)
    if campus_id is not None:
        query = query.where(Teacher.campus_id == campus_id)
    items = db.scalars(query.order_by(Teacher.id.desc())).all()
    return {"items": [public_model(item, ["id", "campus_id", "name", "phone", "title", "status"]) for item in items]}


@router.post("/courses")
def create_course(payload: CourseCreate, db: Session = Depends(get_db)) -> dict:
    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return public_model(
        course,
        ["id", "campus_id", "name", "subject", "default_duration", "default_hour_cost", "status"],
    )


@router.get("/courses")
def courses(campus_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    query = select(Course)
    if campus_id is not None:
        query = query.where(Course.campus_id == campus_id)
    items = db.scalars(query.order_by(Course.id.desc())).all()
    return {
        "items": [
            public_model(
                item,
                ["id", "campus_id", "name", "subject", "default_duration", "default_hour_cost", "status"],
            )
            for item in items
        ]
    }


@router.post("/lessons")
def create_lesson(payload: LessonCreateRequest, db: Session = Depends(get_db)) -> dict:
    lesson_data = payload.model_dump(exclude={"student_ids"})
    lesson = Lesson(**lesson_data)
    db.add(lesson)
    db.flush()
    for student_id in payload.student_ids:
        db.add(
            LessonStudent(
                lesson_id=lesson.id,
                student_id=student_id,
                planned_hour_cost=payload.default_hour_cost,
            )
        )
    db.commit()
    db.refresh(lesson)
    return public_model(
        lesson,
        [
            "id",
            "campus_id",
            "course_id",
            "teacher_id",
            "title",
            "classroom_name",
            "start_time",
            "end_time",
            "status",
        ],
    )


@router.get("/lessons")
def lessons(campus_id: int, db: Session = Depends(get_db)) -> dict:
    items = db.scalars(select(Lesson).where(Lesson.campus_id == campus_id).order_by(Lesson.start_time.desc())).all()
    return {
        "items": [
            public_model(
                item,
                [
                    "id",
                    "campus_id",
                    "course_id",
                    "teacher_id",
                    "title",
                    "classroom_name",
                    "start_time",
                    "end_time",
                    "status",
                ],
            )
            for item in items
        ]
    }


@router.post("/hour-accounts")
def create_hour_account(payload: HourAccountCreate, db: Session = Depends(get_db)) -> dict:
    account = HourService(db).create_account(
        campus_id=payload.campus_id,
        student_id=payload.student_id,
        course_id=payload.course_id,
        initial_hours=payload.initial_hours,
        operator_user_id=None,
        reason=payload.reason,
    )
    db.commit()
    db.refresh(account)
    return public_model(account, ["id", "campus_id", "student_id", "course_id", "balance_hours", "status"])


@router.post("/hour-accounts/{account_id}/ledger")
def create_hour_ledger(account_id: int, payload: HourLedgerCreate, db: Session = Depends(get_db)) -> dict:
    result = HourService(db).create_ledger(
        account_id=account_id,
        change_type=payload.change_type,
        change_hours=payload.change_hours,
        operator_user_id=payload.operator_user_id,
        source="campus_manual",
        reason=payload.reason,
    )
    db.commit()
    return {
        "ledger_id": result.ledger_id,
        "balance_before": float(result.balance_before),
        "balance_after": float(result.balance_after),
    }


@router.get("/hour-ledgers")
def hour_ledgers(campus_id: int, student_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    query = select(HourLedger).where(HourLedger.campus_id == campus_id)
    if student_id is not None:
        query = query.where(HourLedger.student_id == student_id)
    items = db.scalars(query.order_by(HourLedger.id.desc()).limit(100)).all()
    return {
        "items": [
            public_model(
                item,
                [
                    "id",
                    "campus_id",
                    "student_id",
                    "course_id",
                    "lesson_id",
                    "change_type",
                    "change_hours",
                    "balance_before",
                    "balance_after",
                    "source",
                    "reason",
                    "created_at",
                ],
            )
            for item in items
        ]
    }


@router.post("/deduction-rules")
def upsert_deduction_rule(payload: DeductionRuleUpsert, db: Session = Depends(get_db)) -> dict:
    rule = db.scalar(
        select(DeductionRule).where(
            DeductionRule.campus_id == payload.campus_id,
            DeductionRule.scope_type == payload.scope_type,
            DeductionRule.scope_id == payload.scope_id,
        )
    )
    if rule is None:
        rule = DeductionRule(**payload.model_dump())
        db.add(rule)
    else:
        for field, value in payload.model_dump().items():
            setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return public_model(
        rule,
        [
            "id",
            "campus_id",
            "scope_type",
            "scope_id",
            "present_action",
            "late_action",
            "absent_action",
            "leave_action",
            "exception_action",
        ],
    )


@router.post("/devices")
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)) -> dict:
    data = payload.model_dump(exclude={"device_secret"})
    data["secret_hash"] = hashlib.sha256(payload.device_secret.encode("utf-8")).hexdigest()
    device = Device(**data)
    db.add(device)
    db.commit()
    db.refresh(device)
    return public_model(
        device,
        ["id", "campus_id", "device_code", "name", "device_type", "location_type", "location_name", "status"],
    )


@router.get("/devices")
def devices(campus_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    query = select(Device)
    if campus_id is not None:
        query = query.where(Device.campus_id == campus_id)
    items = db.scalars(query.order_by(Device.id.desc())).all()
    return {
        "items": [
            public_model(
                item,
                [
                    "id",
                    "campus_id",
                    "device_code",
                    "name",
                    "device_type",
                    "location_type",
                    "location_name",
                    "status",
                    "last_seen_at",
                ],
            )
            for item in items
        ]
    }
