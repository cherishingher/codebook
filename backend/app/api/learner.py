from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
def learner_dashboard(student_id: int) -> dict:
    return {
        "student": {"id": student_id, "name": ""},
        "today_lessons": [],
        "hour_summary": [],
    }


@router.get("/lessons")
def learner_lessons(student_id: int, start_date: str, end_date: str) -> dict:
    return {"student_id": student_id, "start_date": start_date, "end_date": end_date, "items": []}


@router.get("/hour-ledgers")
def learner_hour_ledgers(student_id: int, page: int = 1, page_size: int = 20) -> dict:
    return {"student_id": student_id, "page": page, "page_size": page_size, "items": []}

