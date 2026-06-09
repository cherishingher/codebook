from fastapi import APIRouter, Depends

from app.core.permissions import Actor, get_current_actor, require_any_role, require_role
from app.core.init_db import init_db
from app.jobs.absence_job import run_absence_job

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/dev/init-db")
def dev_init_db(actor: Actor = Depends(get_current_actor)) -> dict[str, str]:
    require_role(actor, {"super_admin"})
    init_db()
    return {"status": "initialized"}


@router.post("/dev/run-absence-job")
def dev_run_absence_job(actor: Actor = Depends(get_current_actor)) -> dict[str, int]:
    require_any_role(actor, {"campus_admin"})
    return {"created": run_absence_job()}
