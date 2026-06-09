import os
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./codebook_test.sqlite3"

from app.core.database import Base, engine  # noqa: E402
from app.core.init_db import init_db  # noqa: E402
from app.main import app  # noqa: E402


def client() -> TestClient:
    Base.metadata.drop_all(bind=engine)
    init_db()
    return TestClient(app)


def seed_base(client: TestClient, suffix: str = "A") -> dict:
    campus = client.post("/api/v1/campus/campuses", json={"name": f"{suffix}校区", "code": suffix}).json()
    student = client.post(
        "/api/v1/campus/students",
        json={"campus_id": campus["id"], "name": "李明", "student_no": f"S{suffix}001"},
    ).json()
    teacher = client.post(
        "/api/v1/campus/teachers",
        json={"campus_id": campus["id"], "name": "王老师"},
    ).json()
    course = client.post(
        "/api/v1/campus/courses",
        json={"campus_id": campus["id"], "name": "数学一对一", "default_hour_cost": "1.00"},
    ).json()
    account = client.post(
        "/api/v1/campus/hour-accounts",
        json={
            "campus_id": campus["id"],
            "student_id": student["id"],
            "course_id": course["id"],
            "initial_hours": "20.00",
            "reason": "购买20课时",
        },
    ).json()
    client.post("/api/v1/campus/deduction-rules", json={"campus_id": campus["id"]}).raise_for_status()
    client.post(
        "/api/v1/campus/devices",
        json={
            "campus_id": campus["id"],
            "device_code": f"MAC-{suffix}",
            "name": "前台摄像头",
            "device_secret": "secret",
        },
    ).raise_for_status()
    return {
        "campus": campus,
        "student": student,
        "teacher": teacher,
        "course": course,
        "account": account,
        "device_code": f"MAC-{suffix}",
    }


def create_lesson(client: TestClient, data: dict, now: datetime | None = None, past: bool = False) -> dict:
    base_time = (now or datetime.now()).replace(microsecond=0)
    if past:
        start_time = base_time - timedelta(hours=2)
        end_time = base_time - timedelta(minutes=30)
        checkin_start_time = base_time - timedelta(hours=3)
        checkin_end_time = base_time - timedelta(hours=1)
        late_after_time = base_time - timedelta(hours=2) + timedelta(minutes=5)
        title = "数学补课"
    else:
        start_time = base_time + timedelta(minutes=5)
        end_time = base_time + timedelta(minutes=95)
        checkin_start_time = base_time - timedelta(minutes=10)
        checkin_end_time = base_time + timedelta(minutes=30)
        late_after_time = base_time + timedelta(minutes=10)
        title = "数学一对一"

    response = client.post(
        "/api/v1/campus/lessons",
        json={
            "campus_id": data["campus"]["id"],
            "course_id": data["course"]["id"],
            "teacher_id": data["teacher"]["id"],
            "title": title,
            "classroom_name": "A101",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "checkin_start_time": checkin_start_time.isoformat(),
            "checkin_end_time": checkin_end_time.isoformat(),
            "late_after_time": late_after_time.isoformat(),
            "default_hour_cost": "1.00",
            "student_ids": [data["student"]["id"]],
        },
    )
    response.raise_for_status()
    return response.json()


def account_balance(client: TestClient, data: dict) -> float:
    accounts = client.get(
        f"/api/v1/campus/hour-accounts?campus_id={data['campus']['id']}"
        f"&student_id={data['student']['id']}"
    ).json()
    return accounts["items"][0]["balance_hours"]


def test_face_punch_deducts_lesson_hours_and_absence_job() -> None:
    api = client()
    data = seed_base(api, "AUTO")
    now = datetime.now().replace(microsecond=0)
    lesson = create_lesson(api, data, now=now)

    punch = api.post(
        "/api/v1/device/punch-events",
        json={
            "device_code": data["device_code"],
            "local_event_id": "evt-1",
            "student_id": data["student"]["id"],
            "captured_at": now.isoformat(),
            "confidence": "0.95",
        },
    ).json()

    assert punch["matched_lesson_id"] == lesson["id"]
    assert punch["attendance_status"] == "present"
    assert punch["deduction_status"] == "deducted"

    duplicate = api.post(
        "/api/v1/device/punch-events",
        json={
            "device_code": data["device_code"],
            "local_event_id": "evt-1",
            "student_id": data["student"]["id"],
            "captured_at": now.isoformat(),
            "confidence": "0.95",
        },
    ).json()
    assert duplicate["attendance_status"] == "duplicate"

    ledgers = api.get(f"/api/v1/learner/hour-ledgers?student_id={data['student']['id']}").json()
    deductions = [item for item in ledgers["items"] if item["change_type"] == "deduct"]
    assert len(deductions) == 1
    assert deductions[0]["balance_before"] == 20.0
    assert deductions[0]["balance_after"] == 19.0

    missed_lesson = create_lesson(api, data, now=now, past=True)
    absence_job = api.post("/api/v1/dev/run-absence-job").json()
    assert absence_job["created"] == 1

    missed_detail = api.get(
        f"/api/v1/learner/lessons/{missed_lesson['id']}?student_id={data['student']['id']}"
    ).json()
    assert missed_detail["lesson_student"]["attendance_status"] == "absent"
    assert missed_detail["lesson_student"]["deduction_status"] == "manual_required"


def test_teacher_confirmation_restores_and_rededucts_hours() -> None:
    api = client()
    data = seed_base(api, "MANUAL")
    now = datetime.now().replace(microsecond=0)
    lesson = create_lesson(api, data, now=now)

    api.post(
        "/api/v1/device/punch-events",
        json={
            "device_code": data["device_code"],
            "local_event_id": "evt-manual-1",
            "student_id": data["student"]["id"],
            "captured_at": now.isoformat(),
            "confidence": "0.95",
        },
    ).raise_for_status()
    assert account_balance(api, data) == 19.0

    api.post(
        f"/api/v1/teacher/lessons/{lesson['id']}/attendance/confirm",
        json={
            "teacher_id": data["teacher"]["id"],
            "student_id": data["student"]["id"],
            "attendance_status": "absent",
            "deduction_action": "manual_required",
            "reason": "老师确认缺勤",
        },
    ).raise_for_status()
    assert account_balance(api, data) == 20.0

    detail = api.get(
        f"/api/v1/teacher/lessons/{lesson['id']}?teacher_id={data['teacher']['id']}"
    ).json()
    assert detail["students"][0]["attendance_status"] == "absent"
    assert detail["students"][0]["deduction_status"] == "manual_required"
    assert detail["students"][0]["deducted_hours"] == 0.0

    api.post(
        f"/api/v1/teacher/lessons/{lesson['id']}/attendance/confirm",
        json={
            "teacher_id": data["teacher"]["id"],
            "student_id": data["student"]["id"],
            "attendance_status": "present",
            "deduction_action": "deduct",
            "reason": "改回到课并消课",
        },
    ).raise_for_status()
    assert account_balance(api, data) == 19.0

    ledgers = api.get(
        f"/api/v1/campus/hour-ledgers?campus_id={data['campus']['id']}"
        f"&student_id={data['student']['id']}"
    ).json()
    assert [item["change_type"] for item in ledgers["items"]].count("restore") == 1
    assert [item["change_type"] for item in ledgers["items"]].count("deduct") == 2


def test_management_endpoints_return_lesson_details_and_validate_inputs() -> None:
    api = client()
    data = seed_base(api, "MGMT")
    lesson = create_lesson(api, data)

    campus_detail = api.get(
        f"/api/v1/campus/lessons/{lesson['id']}?campus_id={data['campus']['id']}"
    ).json()
    assert campus_detail["lesson"]["id"] == lesson["id"]
    assert campus_detail["students"][0]["student"]["name"] == "李明"

    rules = api.get(f"/api/v1/campus/deduction-rules?campus_id={data['campus']['id']}").json()
    assert rules["items"][0]["present_action"] == "deduct"

    other_teacher = api.post(
        "/api/v1/campus/teachers",
        json={"campus_id": data["campus"]["id"], "name": "张老师"},
    ).json()
    forbidden = api.get(f"/api/v1/teacher/lessons/{lesson['id']}?teacher_id={other_teacher['id']}")
    assert forbidden.status_code == 403

    invalid = api.post(
        "/api/v1/campus/lessons",
        json={
            "campus_id": data["campus"]["id"],
            "course_id": data["course"]["id"],
            "teacher_id": data["teacher"]["id"],
            "title": "重复学生课次",
            "start_time": datetime.now().isoformat(),
            "end_time": (datetime.now() + timedelta(minutes=60)).isoformat(),
            "checkin_start_time": datetime.now().isoformat(),
            "checkin_end_time": (datetime.now() + timedelta(minutes=20)).isoformat(),
            "late_after_time": (datetime.now() + timedelta(minutes=10)).isoformat(),
            "default_hour_cost": "1.00",
            "student_ids": [data["student"]["id"], data["student"]["id"]],
        },
    )
    assert invalid.status_code == 400
