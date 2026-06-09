from dataclasses import dataclass

from fastapi import HTTPException, status


@dataclass(frozen=True)
class Actor:
    user_id: int
    role: str
    campus_id: int | None = None
    student_id: int | None = None
    teacher_id: int | None = None


def require_campus_scope(actor: Actor, campus_id: int) -> None:
    if actor.role == "super_admin":
        return
    if actor.campus_id != campus_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden campus scope")


def require_role(actor: Actor, roles: set[str]) -> None:
    if actor.role not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden role")

