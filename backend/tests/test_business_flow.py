import os
from datetime import datetime, timedelta

from fastapi.testclient import TestClient


def test_face_punch_deducts_lesson_hours(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite:///{(tmp_path / 'codebook.sqlite3').as_posix()}"

    from app.core.init_db import init_db
    from app.main import app

    init_db()
    client = TestClient(app)

    campus = client.post("/api/v1/campus/campuses", json={"name": "A校区", "code": "A"}).json()
    student = client.post(
        "/api/v1/campus/students",
        json={"campus_id": campus["id"], "name": "李明", "student_no": "S001"},
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
    assert account["balance_hours"] == 20.0

    client.post("/api/v1/campus/deduction-rules", json={"campus_id": campus["id"]}).raise_for_status()
    client.post(
        "/api/v1/campus/devices",
        json={
            "campus_id": campus["id"],
            "device_code": "MAC-001",
            "name": "前台摄像头",
            "device_secret": "secret",
        },
    ).raise_for_status()

    now = datetime.now().replace(microsecond=0)
    lesson = client.post(
        "/api/v1/campus/lessons",
        json={
            "campus_id": campus["id"],
            "course_id": course["id"],
            "teacher_id": teacher["id"],
            "title": "数学一对一",
            "classroom_name": "A101",
            "start_time": (now + timedelta(minutes=5)).isoformat(),
            "end_time": (now + timedelta(minutes=95)).isoformat(),
            "checkin_start_time": (now - timedelta(minutes=10)).isoformat(),
            "checkin_end_time": (now + timedelta(minutes=30)).isoformat(),
            "late_after_time": (now + timedelta(minutes=10)).isoformat(),
            "default_hour_cost": "1.00",
            "student_ids": [student["id"]],
        },
    ).json()

    punch = client.post(
        "/api/v1/device/punch-events",
        json={
            "device_code": "MAC-001",
            "local_event_id": "evt-1",
            "student_id": student["id"],
            "captured_at": now.isoformat(),
            "confidence": "0.95",
        },
    ).json()

    assert punch["matched_lesson_id"] == lesson["id"]
    assert punch["attendance_status"] == "present"
    assert punch["deduction_status"] == "deducted"

    duplicate = client.post(
        "/api/v1/device/punch-events",
        json={
            "device_code": "MAC-001",
            "local_event_id": "evt-1",
            "student_id": student["id"],
            "captured_at": now.isoformat(),
            "confidence": "0.95",
        },
    ).json()
    assert duplicate["attendance_status"] == "duplicate"

    ledgers = client.get(f"/api/v1/learner/hour-ledgers?student_id={student['id']}").json()
    deductions = [item for item in ledgers["items"] if item["change_type"] == "deduct"]
    assert len(deductions) == 1
    assert deductions[0]["balance_before"] == 20.0
    assert deductions[0]["balance_after"] == 19.0

    missed_lesson = client.post(
        "/api/v1/campus/lessons",
        json={
            "campus_id": campus["id"],
            "course_id": course["id"],
            "teacher_id": teacher["id"],
            "title": "数学补课",
            "classroom_name": "A102",
            "start_time": (now - timedelta(hours=2)).isoformat(),
            "end_time": (now - timedelta(minutes=30)).isoformat(),
            "checkin_start_time": (now - timedelta(hours=3)).isoformat(),
            "checkin_end_time": (now - timedelta(hours=1)).isoformat(),
            "late_after_time": (now - timedelta(hours=2, minutes=-5)).isoformat(),
            "default_hour_cost": "1.00",
            "student_ids": [student["id"]],
        },
    ).json()

    absence_job = client.post("/api/v1/dev/run-absence-job").json()
    assert absence_job["created"] == 1

    missed_detail = client.get(
        f"/api/v1/learner/lessons/{missed_lesson['id']}?student_id={student['id']}"
    ).json()
    assert missed_detail["lesson_student"]["attendance_status"] == "absent"
    assert missed_detail["lesson_student"]["deduction_status"] == "manual_required"
