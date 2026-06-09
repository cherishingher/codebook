from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Actor:
    user_id: int
    role: str
    campus_id: int | None = None
    student_id: int | None = None
    teacher_id: int | None = None


def get_current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Actor:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc

    subject = payload.get("sub", "")
    user_id = _user_id_from_subject(subject)
    return Actor(
        user_id=user_id,
        role=payload.get("role", "pending"),
        campus_id=payload.get("campus_id"),
        student_id=payload.get("student_id"),
        teacher_id=payload.get("teacher_id"),
    )


def optional_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Actor | None:
    if credentials is None:
        return None
    return get_current_actor(credentials)


def require_campus_scope(actor: Actor, campus_id: int) -> None:
    if actor.role == "super_admin":
        return
    if actor.campus_id != campus_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden campus scope")


def require_role(actor: Actor, roles: set[str]) -> None:
    if actor.role not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden role")


def _user_id_from_subject(subject: str) -> int:
    if subject.startswith("user:"):
        try:
            return int(subject.split(":", 1)[1])
        except ValueError:
            return 0
    return 0
