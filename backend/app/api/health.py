from fastapi import APIRouter

from app.core.init_db import init_db
from app.jobs.absence_job import run_absence_job

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/dev/init-db")
def dev_init_db() -> dict[str, str]:
    init_db()
    return {"status": "initialized"}


@router.post("/dev/run-absence-job")
def dev_run_absence_job() -> dict[str, int]:
    return {"created": run_absence_job()}
