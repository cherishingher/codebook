from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
def campus_dashboard() -> dict:
    return {
        "today_lessons": 0,
        "expected_attendances": 0,
        "present_count": 0,
        "late_count": 0,
        "absent_count": 0,
        "deducted_hours": 0,
        "pending_exceptions": 0,
        "devices_online": 0,
    }


@router.get("/students")
def students(keyword: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    return {"keyword": keyword, "page": page, "page_size": page_size, "items": []}


@router.get("/devices")
def devices() -> dict:
    return {"items": []}

