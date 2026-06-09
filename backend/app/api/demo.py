from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.utils import public_model
from app.core.database import get_db
from app.core.init_db import init_db
from app.jobs.absence_job import run_absence_job
from app.models.campus import Campus
from app.models.course import Course
from app.models.device import Device
from app.models.hour import DeductionRule, HourAccount, HourLedger
from app.models.lesson import Lesson, LessonStudent
from app.models.student import Student
from app.models.teacher import Teacher
from app.services.attendance_service import AttendanceService
from app.services.hour_service import HourService

router = APIRouter()


@router.get("/demo", response_class=HTMLResponse, include_in_schema=False)
def demo_page() -> str:
    return DEMO_HTML


@router.post("/api/v1/demo/seed")
def seed_demo(db: Session = Depends(get_db)) -> dict:
    init_db()
    data = _ensure_demo_data(db)
    return _state(db, data)


@router.get("/api/v1/demo/state")
def demo_state(db: Session = Depends(get_db)) -> dict:
    init_db()
    data = _ensure_demo_data(db)
    return _state(db, data)


@router.post("/api/v1/demo/punch")
def demo_punch(db: Session = Depends(get_db)) -> dict:
    init_db()
    data = _ensure_demo_data(db)
    result = AttendanceService(db).process_punch_event(
        device_code=data["device"].device_code,
        local_event_id=f"demo-{uuid4()}",
        student_id=data["student"].id,
        captured_at=datetime.now(),
        confidence=Decimal("0.95"),
        snapshot_path=None,
    )
    db.commit()
    return {"punch": result.__dict__, "state": _state(db, data)}


@router.post("/api/v1/demo/new-lesson")
def demo_new_lesson(db: Session = Depends(get_db)) -> dict:
    init_db()
    data = _ensure_demo_data(db)
    _create_active_lesson(db, data)
    db.commit()
    fresh = _ensure_demo_data(db)
    return _state(db, fresh)


@router.post("/api/v1/demo/absence-job")
def demo_absence_job(db: Session = Depends(get_db)) -> dict:
    init_db()
    _ensure_demo_data(db, create_missed_lesson=True)
    created = run_absence_job(db=db)
    db.commit()
    data = _ensure_demo_data(db)
    return {"created": created, "state": _state(db, data)}


def _ensure_demo_data(db: Session, create_missed_lesson: bool = False) -> dict:
    campus = db.scalar(select(Campus).where(Campus.code == "DEMO"))
    if campus is None:
        campus = Campus(name="演示校区", code="DEMO", address="本地 Mac mini")
        db.add(campus)
        db.flush()

    student = db.scalar(select(Student).where(Student.campus_id == campus.id, Student.student_no == "S001"))
    if student is None:
        student = Student(campus_id=campus.id, name="李明", student_no="S001", status="active")
        db.add(student)
        db.flush()

    teacher = db.scalar(select(Teacher).where(Teacher.campus_id == campus.id, Teacher.name == "王老师"))
    if teacher is None:
        teacher = Teacher(campus_id=campus.id, name="王老师", title="数学老师", status="active")
        db.add(teacher)
        db.flush()

    course = db.scalar(select(Course).where(Course.campus_id == campus.id, Course.name == "数学一对一"))
    if course is None:
        course = Course(
            campus_id=campus.id,
            name="数学一对一",
            subject="数学",
            default_duration=90,
            default_hour_cost=Decimal("1.00"),
            status="active",
        )
        db.add(course)
        db.flush()

    account = db.scalar(
        select(HourAccount).where(HourAccount.student_id == student.id, HourAccount.course_id == course.id)
    )
    if account is None:
        account = HourService(db).create_account(
            campus_id=campus.id,
            student_id=student.id,
            course_id=course.id,
            initial_hours=Decimal("20.00"),
            operator_user_id=None,
            reason="演示加课 20 课时",
        )
        db.flush()

    rule = db.scalar(
        select(DeductionRule).where(
            DeductionRule.campus_id == campus.id,
            DeductionRule.scope_type == "campus",
            DeductionRule.scope_id.is_(None),
        )
    )
    if rule is None:
        db.add(DeductionRule(campus_id=campus.id))

    device = db.scalar(select(Device).where(Device.device_code == "DEMO-MAC-001"))
    if device is None:
        device = Device(
            campus_id=campus.id,
            device_code="DEMO-MAC-001",
            name="前台 USB 摄像头",
            location_type="frontdesk",
            location_name="前台",
            secret_hash=hashlib.sha256("demo-secret".encode("utf-8")).hexdigest(),
            status="active",
        )
        db.add(device)
        db.flush()

    now = datetime.now().replace(microsecond=0)
    lesson = db.scalar(
        select(Lesson)
        .join(LessonStudent, LessonStudent.lesson_id == Lesson.id)
        .where(
            Lesson.campus_id == campus.id,
            LessonStudent.student_id == student.id,
            Lesson.checkin_start_time <= now,
            Lesson.checkin_end_time >= now,
            Lesson.status != "cancelled",
        )
        .order_by(Lesson.id.desc())
    )
    if lesson is None:
        lesson = _create_active_lesson(db, {"campus": campus, "student": student, "teacher": teacher, "course": course})

    if create_missed_lesson:
        missed = Lesson(
            campus_id=campus.id,
            course_id=course.id,
            teacher_id=teacher.id,
            title="缺勤演示课次",
            classroom_name="A102",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(minutes=30),
            checkin_start_time=now - timedelta(hours=3),
            checkin_end_time=now - timedelta(hours=1),
            late_after_time=now - timedelta(hours=2) + timedelta(minutes=5),
            default_hour_cost=Decimal("1.00"),
            status="scheduled",
        )
        db.add(missed)
        db.flush()
        db.add(LessonStudent(lesson_id=missed.id, student_id=student.id, planned_hour_cost=Decimal("1.00")))

    db.commit()
    return {"campus": campus, "student": student, "teacher": teacher, "course": course, "account": account, "device": device, "lesson": lesson}


def _create_active_lesson(db: Session, data: dict) -> Lesson:
    now = datetime.now().replace(microsecond=0)
    active_lessons = db.scalars(
        select(Lesson)
        .join(LessonStudent, LessonStudent.lesson_id == Lesson.id)
        .where(
            Lesson.campus_id == data["campus"].id,
            LessonStudent.student_id == data["student"].id,
            Lesson.checkin_start_time <= now,
            Lesson.checkin_end_time >= now,
            Lesson.status != "cancelled",
        )
    ).all()
    for active_lesson in active_lessons:
        active_lesson.status = "cancelled"

    lesson = Lesson(
        campus_id=data["campus"].id,
        course_id=data["course"].id,
        teacher_id=data["teacher"].id,
        title=f"数学一对一 {now.strftime('%H:%M:%S')}",
        classroom_name="A101",
        start_time=now + timedelta(minutes=5),
        end_time=now + timedelta(minutes=95),
        checkin_start_time=now - timedelta(minutes=10),
        checkin_end_time=now + timedelta(minutes=30),
        late_after_time=now + timedelta(minutes=10),
        default_hour_cost=Decimal("1.00"),
        status="scheduled",
    )
    db.add(lesson)
    db.flush()
    db.add(
        LessonStudent(
            lesson_id=lesson.id,
            student_id=data["student"].id,
            planned_hour_cost=Decimal("1.00"),
        )
    )
    db.flush()
    return lesson


def _state(db: Session, data: dict) -> dict:
    account = db.scalar(
        select(HourAccount).where(
            HourAccount.student_id == data["student"].id,
            HourAccount.course_id == data["course"].id,
        )
    )
    lesson_students = db.scalars(
        select(LessonStudent)
        .join(Lesson, Lesson.id == LessonStudent.lesson_id)
        .where(Lesson.campus_id == data["campus"].id, LessonStudent.student_id == data["student"].id)
        .order_by(Lesson.id.desc())
        .limit(5)
    ).all()
    ledgers = db.scalars(
        select(HourLedger)
        .where(HourLedger.student_id == data["student"].id)
        .order_by(HourLedger.id.desc())
        .limit(8)
    ).all()
    return {
        "campus": public_model(data["campus"], ["id", "name", "code"]),
        "student": public_model(data["student"], ["id", "name", "student_no"]),
        "course": public_model(data["course"], ["id", "name", "default_hour_cost"]),
        "teacher": public_model(data["teacher"], ["id", "name", "title"]),
        "device": public_model(data["device"], ["id", "device_code", "name", "location_name", "status"]),
        "account": public_model(account, ["id", "balance_hours", "status"]) if account else None,
        "lesson_students": [
            public_model(
                item,
                [
                    "id",
                    "lesson_id",
                    "student_id",
                    "attendance_status",
                    "deduction_status",
                    "deducted_hours",
                    "note",
                ],
            )
            for item in lesson_students
        ],
        "ledgers": [
            public_model(
                item,
                [
                    "id",
                    "change_type",
                    "change_hours",
                    "balance_before",
                    "balance_after",
                    "source",
                    "reason",
                    "created_at",
                ],
            )
            for item in ledgers
        ],
    }


DEMO_HTML = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Codebook 演示</title>
  <style>
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f7fb; color: #111827; }
    header { background: #0f172a; color: white; padding: 22px 28px; }
    main { padding: 24px; max-width: 1120px; margin: 0 auto; }
    h1 { margin: 0 0 6px; font-size: 26px; }
    .sub { color: #cbd5e1; }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-bottom: 18px; }
    .card { background: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 18px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
    .label { color: #6b7280; font-size: 13px; margin-bottom: 8px; }
    .value { font-size: 28px; font-weight: 700; }
    .actions { display: flex; gap: 12px; flex-wrap: wrap; margin: 18px 0; }
    button { border: 0; border-radius: 8px; padding: 11px 16px; color: white; background: #2563eb; font-weight: 600; cursor: pointer; }
    button.secondary { background: #475569; }
    button.warn { background: #b45309; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
    th, td { padding: 12px 14px; border-bottom: 1px solid #e5e7eb; text-align: left; font-size: 14px; }
    th { background: #f8fafc; color: #475569; }
    .ok { color: #15803d; font-weight: 700; }
    .pending { color: #b45309; font-weight: 700; }
    .section { margin-top: 22px; }
    pre { background: #0f172a; color: #e5e7eb; padding: 14px; border-radius: 10px; overflow: auto; }
    @media (max-width: 800px) { .grid { grid-template-columns: 1fr; } main { padding: 16px; } }
  </style>
</head>
<body>
  <header>
    <h1>Codebook 本地演示</h1>
    <div class="sub">Mac mini + USB 摄像头 + 课次考勤 + 自动消课核心闭环</div>
  </header>
  <main>
    <div class="actions">
      <button onclick="seed()">生成/刷新演示数据</button>
      <button class="secondary" onclick="newLesson()">新建一节可打卡课次</button>
      <button onclick="punch()">模拟 USB 摄像头打卡</button>
      <button class="warn" onclick="absence()">运行缺勤任务</button>
      <button class="secondary" onclick="loadState()">刷新页面数据</button>
    </div>
    <div class="grid">
      <div class="card"><div class="label">学员</div><div class="value" id="student">-</div></div>
      <div class="card"><div class="label">课程</div><div class="value" id="course">-</div></div>
      <div class="card"><div class="label">剩余课时</div><div class="value" id="balance">-</div></div>
    </div>
    <div class="grid">
      <div class="card"><div class="label">校区</div><div class="value" id="campus">-</div></div>
      <div class="card"><div class="label">教师</div><div class="value" id="teacher">-</div></div>
      <div class="card"><div class="label">设备</div><div class="value" id="device">-</div></div>
    </div>
    <div class="section">
      <h2>最近课次状态</h2>
      <table>
        <thead><tr><th>课次ID</th><th>考勤</th><th>消课</th><th>已消课时</th><th>备注</th></tr></thead>
        <tbody id="lessonRows"></tbody>
      </table>
    </div>
    <div class="section">
      <h2>课时流水</h2>
      <table>
        <thead><tr><th>ID</th><th>类型</th><th>变化</th><th>变动前</th><th>变动后</th><th>来源</th><th>原因</th></tr></thead>
        <tbody id="ledgerRows"></tbody>
      </table>
    </div>
    <div class="section">
      <h2>最近操作结果</h2>
      <pre id="result">等待操作...</pre>
    </div>
  </main>
  <script>
    async function api(path, options = {}) {
      const res = await fetch(path, { method: options.method || 'GET', headers: { 'Content-Type': 'application/json' } });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    }
    function statusClass(value) {
      return value === 'deducted' || value === 'present' || value === 'late' ? 'ok' : 'pending';
    }
    function render(state) {
      document.getElementById('student').textContent = state.student.name;
      document.getElementById('course').textContent = state.course.name;
      document.getElementById('balance').textContent = `${Number(state.account.balance_hours).toFixed(2)} 课时`;
      document.getElementById('campus').textContent = state.campus.name;
      document.getElementById('teacher').textContent = state.teacher.name;
      document.getElementById('device').textContent = state.device.name;
      document.getElementById('lessonRows').innerHTML = state.lesson_students.map(item => `
        <tr>
          <td>${item.lesson_id}</td>
          <td class="${statusClass(item.attendance_status)}">${item.attendance_status}</td>
          <td class="${statusClass(item.deduction_status)}">${item.deduction_status}</td>
          <td>${Number(item.deducted_hours || 0).toFixed(2)}</td>
          <td>${item.note || ''}</td>
        </tr>`).join('');
      document.getElementById('ledgerRows').innerHTML = state.ledgers.map(item => `
        <tr>
          <td>${item.id}</td>
          <td>${item.change_type}</td>
          <td>${Number(item.change_hours).toFixed(2)}</td>
          <td>${Number(item.balance_before).toFixed(2)}</td>
          <td>${Number(item.balance_after).toFixed(2)}</td>
          <td>${item.source}</td>
          <td>${item.reason || ''}</td>
        </tr>`).join('');
    }
    async function loadState() {
      const state = await api('/api/v1/demo/state');
      render(state);
      return state;
    }
    async function seed() {
      const data = await api('/api/v1/demo/seed', { method: 'POST' });
      document.getElementById('result').textContent = JSON.stringify(data, null, 2);
      await loadState();
    }
    async function punch() {
      const data = await api('/api/v1/demo/punch', { method: 'POST' });
      document.getElementById('result').textContent = JSON.stringify(data.punch, null, 2);
      render(data.state);
    }
    async function newLesson() {
      const state = await api('/api/v1/demo/new-lesson', { method: 'POST' });
      document.getElementById('result').textContent = '已新建一节可打卡课次，现在可以模拟 USB 摄像头打卡。';
      render(state);
    }
    async function absence() {
      const data = await api('/api/v1/demo/absence-job', { method: 'POST' });
      document.getElementById('result').textContent = JSON.stringify({ created: data.created }, null, 2);
      render(data.state);
    }
    loadState().catch(err => document.getElementById('result').textContent = err.message);
  </script>
</body>
</html>
"""
