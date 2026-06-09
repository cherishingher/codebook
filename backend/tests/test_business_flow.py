import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import os
import uuid

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./codebook_test.sqlite3"

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.init_db import init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.device import Device  # noqa: E402
from app.models.face import FaceProfile  # noqa: E402


DEVICE_SECRET = "secret"


def client() -> TestClient:
    Base.metadata.drop_all(bind=engine)
    init_db()
    return TestClient(app)


def auth_headers(
    client: TestClient,
    *,
    role: str,
    openid: str,
    campus_id: int | None = None,
    student_id: int | None = None,
    teacher_id: int | None = None,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/local-login",
        json={
            "openid": openid,
            "name": openid,
            "role": role,
            "campus_id": campus_id,
            "student_id": student_id,
            "teacher_id": teacher_id,
        },
    )
    response.raise_for_status()
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def json_body(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def signed_device_headers(
    *,
    device_code: str,
    secret: str,
    body: bytes = b"",
    nonce: str | None = None,
    timestamp: datetime | None = None,
) -> dict[str, str]:
    signed_at = (timestamp or datetime.now(UTC)).isoformat()
    signed_nonce = nonce or str(uuid.uuid4())
    signature_key = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    signing_payload = f"{signed_at}.{signed_nonce}.".encode("utf-8") + body
    signature = hmac.new(signature_key.encode("utf-8"), signing_payload, hashlib.sha256).hexdigest()
    return {
        "X-Codebook-Device-Code": device_code,
        "X-Codebook-Timestamp": signed_at,
        "X-Codebook-Nonce": signed_nonce,
        "X-Codebook-Signature": signature,
    }


def signed_device_post(
    client: TestClient,
    path: str,
    *,
    device_code: str,
    secret: str,
    payload: dict,
    nonce: str | None = None,
    timestamp: datetime | None = None,
) -> object:
    body = json_body(payload)
    headers = signed_device_headers(
        device_code=device_code,
        secret=secret,
        body=body,
        nonce=nonce,
        timestamp=timestamp,
    )
    headers["Content-Type"] = "application/json"
    return client.post(path, content=body, headers=headers)


def signed_device_get(
    client: TestClient,
    path: str,
    *,
    device_code: str,
    secret: str,
    nonce: str | None = None,
    timestamp: datetime | None = None,
) -> object:
    return client.get(
        path,
        headers=signed_device_headers(
            device_code=device_code,
            secret=secret,
            nonce=nonce,
            timestamp=timestamp,
        ),
    )


def seed_base(client: TestClient, suffix: str = "A") -> dict:
    super_headers = auth_headers(client, role="super_admin", openid=f"local:{suffix}:super")
    campus = client.post(
        "/api/v1/campus/campuses",
        headers=super_headers,
        json={"name": f"{suffix} Campus", "code": suffix},
    ).json()

    campus_headers = auth_headers(
        client,
        role="campus_admin",
        openid=f"local:{suffix}:campus-admin",
        campus_id=campus["id"],
    )
    student = client.post(
        "/api/v1/campus/students",
        headers=campus_headers,
        json={"campus_id": campus["id"], "name": "Li Ming", "student_no": f"S{suffix}001"},
    ).json()
    teacher = client.post(
        "/api/v1/campus/teachers",
        headers=campus_headers,
        json={"campus_id": campus["id"], "name": "Wang Teacher"},
    ).json()
    course = client.post(
        "/api/v1/campus/courses",
        headers=campus_headers,
        json={"campus_id": campus["id"], "name": "Math 1v1", "default_hour_cost": "1.00"},
    ).json()
    account = client.post(
        "/api/v1/campus/hour-accounts",
        headers=campus_headers,
        json={
            "campus_id": campus["id"],
            "student_id": student["id"],
            "course_id": course["id"],
            "initial_hours": "20.00",
            "reason": "Purchased 20 hours",
        },
    ).json()
    client.post(
        "/api/v1/campus/deduction-rules",
        headers=campus_headers,
        json={"campus_id": campus["id"]},
    ).raise_for_status()
    client.post(
        "/api/v1/campus/devices",
        headers=campus_headers,
        json={
            "campus_id": campus["id"],
            "device_code": f"MAC-{suffix}",
            "name": "Front Desk Camera",
            "device_secret": DEVICE_SECRET,
        },
    ).raise_for_status()

    teacher_headers = auth_headers(
        client,
        role="teacher",
        openid=f"local:{suffix}:teacher",
        campus_id=campus["id"],
        teacher_id=teacher["id"],
    )
    learner_headers = auth_headers(
        client,
        role="learner",
        openid=f"local:{suffix}:learner",
        student_id=student["id"],
    )
    return {
        "campus": campus,
        "student": student,
        "teacher": teacher,
        "course": course,
        "account": account,
        "device_code": f"MAC-{suffix}",
        "device_secret": DEVICE_SECRET,
        "super_headers": super_headers,
        "campus_headers": campus_headers,
        "teacher_headers": teacher_headers,
        "learner_headers": learner_headers,
    }


def create_lesson(client: TestClient, data: dict, now: datetime | None = None, past: bool = False) -> dict:
    base_time = (now or datetime.now()).replace(microsecond=0)
    if past:
        start_time = base_time - timedelta(hours=2)
        end_time = base_time - timedelta(minutes=30)
        checkin_start_time = base_time - timedelta(hours=3)
        checkin_end_time = base_time - timedelta(hours=1)
        late_after_time = base_time - timedelta(hours=2) + timedelta(minutes=5)
        title = "Math makeup lesson"
    else:
        start_time = base_time + timedelta(minutes=5)
        end_time = base_time + timedelta(minutes=95)
        checkin_start_time = base_time - timedelta(minutes=10)
        checkin_end_time = base_time + timedelta(minutes=30)
        late_after_time = base_time + timedelta(minutes=10)
        title = "Math 1v1"

    response = client.post(
        "/api/v1/campus/lessons",
        headers=data["campus_headers"],
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
        f"&student_id={data['student']['id']}",
        headers=data["campus_headers"],
    ).json()
    return accounts["items"][0]["balance_hours"]


def punch_payload(data: dict, local_event_id: str, captured_at: datetime) -> dict:
    return {
        "device_code": data["device_code"],
        "local_event_id": local_event_id,
        "student_id": data["student"]["id"],
        "captured_at": captured_at.isoformat(),
        "confidence": "0.95",
    }


def post_signed_punch(client: TestClient, data: dict, payload: dict) -> object:
    return signed_device_post(
        client,
        "/api/v1/device/punch-events",
        device_code=data["device_code"],
        secret=data["device_secret"],
        payload=payload,
    )


def test_face_punch_deducts_lesson_hours_and_absence_job() -> None:
    api = client()
    data = seed_base(api, "AUTO")
    now = datetime.now().replace(microsecond=0)
    lesson = create_lesson(api, data, now=now)

    punch = post_signed_punch(api, data, punch_payload(data, "evt-1", now)).json()

    assert punch["matched_lesson_id"] == lesson["id"]
    assert punch["attendance_status"] == "present"
    assert punch["deduction_status"] == "deducted"

    duplicate = post_signed_punch(api, data, punch_payload(data, "evt-1", now)).json()
    assert duplicate["attendance_status"] == "duplicate"

    ledgers = api.get(
        f"/api/v1/learner/hour-ledgers?student_id={data['student']['id']}",
        headers=data["learner_headers"],
    ).json()
    deductions = [item for item in ledgers["items"] if item["change_type"] == "deduct"]
    assert len(deductions) == 1
    assert deductions[0]["balance_before"] == 20.0
    assert deductions[0]["balance_after"] == 19.0

    missed_lesson = create_lesson(api, data, now=now, past=True)
    absence_job = api.post("/api/v1/dev/run-absence-job", headers=data["campus_headers"]).json()
    assert absence_job["created"] == 1

    missed_detail = api.get(
        f"/api/v1/learner/lessons/{missed_lesson['id']}?student_id={data['student']['id']}",
        headers=data["learner_headers"],
    ).json()
    assert missed_detail["lesson_student"]["attendance_status"] == "absent"
    assert missed_detail["lesson_student"]["deduction_status"] == "manual_required"


def test_teacher_confirmation_restores_and_rededucts_hours() -> None:
    api = client()
    data = seed_base(api, "MANUAL")
    now = datetime.now().replace(microsecond=0)
    lesson = create_lesson(api, data, now=now)

    post_signed_punch(api, data, punch_payload(data, "evt-manual-1", now)).raise_for_status()
    assert account_balance(api, data) == 19.0

    api.post(
        f"/api/v1/teacher/lessons/{lesson['id']}/attendance/confirm",
        headers=data["teacher_headers"],
        json={
            "teacher_id": data["teacher"]["id"],
            "student_id": data["student"]["id"],
            "attendance_status": "absent",
            "deduction_action": "manual_required",
            "reason": "Teacher confirmed absent",
        },
    ).raise_for_status()
    assert account_balance(api, data) == 20.0

    detail = api.get(
        f"/api/v1/teacher/lessons/{lesson['id']}?teacher_id={data['teacher']['id']}",
        headers=data["teacher_headers"],
    ).json()
    assert detail["students"][0]["attendance_status"] == "absent"
    assert detail["students"][0]["deduction_status"] == "manual_required"
    assert detail["students"][0]["deducted_hours"] == 0.0

    api.post(
        f"/api/v1/teacher/lessons/{lesson['id']}/attendance/confirm",
        headers=data["teacher_headers"],
        json={
            "teacher_id": data["teacher"]["id"],
            "student_id": data["student"]["id"],
            "attendance_status": "present",
            "deduction_action": "deduct",
            "reason": "Changed back to present",
        },
    ).raise_for_status()
    assert account_balance(api, data) == 19.0

    ledgers = api.get(
        f"/api/v1/campus/hour-ledgers?campus_id={data['campus']['id']}"
        f"&student_id={data['student']['id']}",
        headers=data["campus_headers"],
    ).json()
    assert [item["change_type"] for item in ledgers["items"]].count("restore") == 1
    assert [item["change_type"] for item in ledgers["items"]].count("deduct") == 2


def test_management_endpoints_return_lesson_details_and_validate_inputs() -> None:
    api = client()
    data = seed_base(api, "MGMT")
    lesson = create_lesson(api, data)

    campus_detail = api.get(
        f"/api/v1/campus/lessons/{lesson['id']}?campus_id={data['campus']['id']}",
        headers=data["campus_headers"],
    ).json()
    assert campus_detail["lesson"]["id"] == lesson["id"]
    assert campus_detail["students"][0]["student"]["name"] == "Li Ming"

    rules = api.get(
        f"/api/v1/campus/deduction-rules?campus_id={data['campus']['id']}",
        headers=data["campus_headers"],
    ).json()
    assert rules["items"][0]["present_action"] == "deduct"

    teacher_courses = api.get(
        f"/api/v1/campus/courses?campus_id={data['campus']['id']}",
        headers=data["teacher_headers"],
    )
    assert teacher_courses.status_code == 200
    assert teacher_courses.json()["items"][0]["name"] == "Math 1v1"

    teacher_students = api.get(
        f"/api/v1/campus/students?campus_id={data['campus']['id']}",
        headers=data["teacher_headers"],
    )
    assert teacher_students.status_code == 200
    assert teacher_students.json()["items"][0]["name"] == "Li Ming"

    teacher_write = api.post(
        "/api/v1/campus/students",
        headers=data["teacher_headers"],
        json={"campus_id": data["campus"]["id"], "name": "Teacher Write Blocked"},
    )
    assert teacher_write.status_code == 403

    other_teacher = api.post(
        "/api/v1/campus/teachers",
        headers=data["campus_headers"],
        json={"campus_id": data["campus"]["id"], "name": "Zhang Teacher"},
    ).json()
    forbidden = api.get(
        f"/api/v1/teacher/lessons/{lesson['id']}?teacher_id={other_teacher['id']}",
        headers=data["teacher_headers"],
    )
    assert forbidden.status_code == 403

    unauthorized = api.get(f"/api/v1/campus/lessons/{lesson['id']}?campus_id={data['campus']['id']}")
    assert unauthorized.status_code == 401

    invalid = api.post(
        "/api/v1/campus/lessons",
        headers=data["campus_headers"],
        json={
            "campus_id": data["campus"]["id"],
            "course_id": data["course"]["id"],
            "teacher_id": data["teacher"]["id"],
            "title": "Duplicate student lesson",
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


def test_local_login_issues_token_and_switches_bound_role() -> None:
    api = client()
    data = seed_base(api, "AUTH")
    login = api.post(
        "/api/v1/auth/local-login",
        json={
            "openid": "local:campus-admin",
            "name": "Campus Admin",
            "role": "campus_admin",
            "campus_id": data["campus"]["id"],
        },
    ).json()
    assert login["token"]
    assert any(item["role"] == "campus_admin" for item in login["roles"])

    switched = api.post(
        "/api/v1/auth/switch-role",
        headers={"Authorization": f"Bearer {login['token']}"},
        json={"role": "campus_admin", "campus_id": data["campus"]["id"]},
    )
    assert switched.status_code == 200
    assert switched.json()["token"]

    forbidden = api.post(
        "/api/v1/auth/switch-role",
        headers={"Authorization": f"Bearer {login['token']}"},
        json={"role": "campus_admin", "campus_id": data["campus"]["id"] + 100},
    )
    assert forbidden.status_code == 403

    teacher_login = api.post(
        "/api/v1/auth/local-login",
        json={
            "openid": "local:teacher-role",
            "name": "Teacher Role",
            "role": "teacher",
            "campus_id": data["campus"]["id"],
            "teacher_id": data["teacher"]["id"],
        },
    ).json()
    teacher_roles = teacher_login["roles"]
    assert {"role": "teacher", "campus_id": data["campus"]["id"], "teacher_id": data["teacher"]["id"]} in teacher_roles
    assert not any(item["role"] == "teacher" and "teacher_id" not in item for item in teacher_roles)

    missing_scope = api.post(
        "/api/v1/auth/switch-role",
        headers={"Authorization": f"Bearer {teacher_login['token']}"},
        json={"role": "teacher", "campus_id": data["campus"]["id"]},
    )
    assert missing_scope.status_code == 403

    teacher_switched = api.post(
        "/api/v1/auth/switch-role",
        headers={"Authorization": f"Bearer {teacher_login['token']}"},
        json={"role": "teacher", "campus_id": data["campus"]["id"], "teacher_id": data["teacher"]["id"]},
    )
    assert teacher_switched.status_code == 200


def test_device_face_profile_sync_returns_persisted_features() -> None:
    api = client()
    data = seed_base(api, "FACE")
    feature = b"\x00\x00\x80?\x00\x00\x00?"

    with SessionLocal() as session:
        session.add(
            FaceProfile(
                campus_id=data["campus"]["id"],
                student_id=data["student"]["id"],
                feature_data=feature,
                feature_version="simple-32x32",
                consent_status="granted",
                status="active",
            )
        )
        session.commit()

    response = signed_device_get(
        api,
        f"/api/v1/device/face-profiles?device_code={data['device_code']}",
        device_code=data["device_code"],
        secret=data["device_secret"],
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["student_id"] == data["student"]["id"]
    assert base64.b64decode(items[0]["feature_data"]) == feature


def test_device_hmac_rejects_missing_bad_expired_and_replayed_signatures() -> None:
    api = client()
    data = seed_base(api, "HMAC")
    payload = {
        "device_code": data["device_code"],
        "timestamp": datetime.now().isoformat(),
        "camera_status": "ok",
    }

    missing = api.post("/api/v1/device/heartbeat", json=payload)
    assert missing.status_code == 401

    body = json_body(payload)
    bad_headers = signed_device_headers(
        device_code=data["device_code"],
        secret=data["device_secret"],
        body=body,
    )
    bad_headers["X-Codebook-Signature"] = "bad"
    bad_headers["Content-Type"] = "application/json"
    bad = api.post("/api/v1/device/heartbeat", content=body, headers=bad_headers)
    assert bad.status_code == 401

    expired = signed_device_post(
        api,
        "/api/v1/device/heartbeat",
        device_code=data["device_code"],
        secret=data["device_secret"],
        payload=payload,
        timestamp=datetime.now(UTC) - timedelta(minutes=10),
    )
    assert expired.status_code == 401

    replay_nonce = "same-nonce"
    first = signed_device_post(
        api,
        "/api/v1/device/heartbeat",
        device_code=data["device_code"],
        secret=data["device_secret"],
        payload=payload,
        nonce=replay_nonce,
    )
    assert first.status_code == 200
    replay = signed_device_post(
        api,
        "/api/v1/device/heartbeat",
        device_code=data["device_code"],
        secret=data["device_secret"],
        payload=payload,
        nonce=replay_nonce,
    )
    assert replay.status_code == 409

    with SessionLocal() as session:
        device = session.query(Device).filter(Device.device_code == data["device_code"]).one()
        device.status = "inactive"
        session.commit()

    inactive = signed_device_post(
        api,
        "/api/v1/device/heartbeat",
        device_code=data["device_code"],
        secret=data["device_secret"],
        payload=payload,
    )
    assert inactive.status_code == 403
