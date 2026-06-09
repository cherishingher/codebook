from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen
import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.utils import public_model
from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import Actor, get_current_actor
from app.core.security import create_access_token
from app.models.student import GuardianStudentRelation
from app.models.teacher import Teacher
from app.models.user import User, UserRole

router = APIRouter()


class WechatLoginRequest(BaseModel):
    code: str


class LocalLoginRequest(BaseModel):
    openid: str
    name: str | None = None
    role: str
    campus_id: int | None = None
    student_id: int | None = None
    teacher_id: int | None = None


class SwitchRoleRequest(BaseModel):
    role: str
    campus_id: int | None = None
    student_id: int | None = None
    teacher_id: int | None = None


@router.post("/wechat-login")
def wechat_login(payload: WechatLoginRequest, db: Session = Depends(get_db)) -> dict:
    openid, unionid = _exchange_wechat_code(payload.code)
    user = _upsert_user(db, openid=openid, unionid=unionid, name=None)
    db.commit()
    db.refresh(user)
    roles = _role_options(db, user)
    token = create_access_token(subject=f"user:{user.id}", claims={"role": "pending"})
    return {
        "token": token,
        "user": public_model(user, ["id", "openid", "name", "phone", "status"]),
        "roles": roles,
    }


@router.post("/local-login")
def local_login(payload: LocalLoginRequest, db: Session = Depends(get_db)) -> dict:
    if not settings.enable_local_login:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Local login is disabled")
    user = _upsert_user(db, openid=payload.openid, unionid=None, name=payload.name)
    db.flush()
    _ensure_role(
        db,
        user_id=user.id,
        role=payload.role,
        campus_id=payload.campus_id,
        student_id=payload.student_id,
        teacher_id=payload.teacher_id,
    )
    db.commit()
    db.refresh(user)
    token = _token_for_role(
        user_id=user.id,
        role=payload.role,
        campus_id=payload.campus_id,
        student_id=payload.student_id,
        teacher_id=payload.teacher_id,
    )
    return {
        "token": token,
        "user": public_model(user, ["id", "openid", "name", "phone", "status"]),
        "roles": _role_options(db, user),
    }


@router.post("/switch-role")
def switch_role(
    payload: SwitchRoleRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
) -> dict:
    user = db.get(User, actor.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    roles = _role_options(db, user)
    requested = {
        "role": payload.role,
        "campus_id": payload.campus_id,
        "student_id": payload.student_id,
        "teacher_id": payload.teacher_id,
    }
    if not any(_role_matches(option, requested) for option in roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role is not bound to this user")
    token = _token_for_role(
        user_id=user.id,
        role=payload.role,
        campus_id=payload.campus_id,
        student_id=payload.student_id,
        teacher_id=payload.teacher_id,
    )
    return {"token": token}


def _exchange_wechat_code(code: str) -> tuple[str, str | None]:
    if not settings.wechat_appid or not settings.wechat_secret:
        if settings.environment == "production":
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="WeChat login is not configured")
        return f"dev:{code}", None

    params = urlencode(
        {
            "appid": settings.wechat_appid,
            "secret": settings.wechat_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
    )
    with urlopen(f"https://api.weixin.qq.com/sns/jscode2session?{params}", timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))
    if "openid" not in data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=data.get("errmsg", "WeChat login failed"))
    return data["openid"], data.get("unionid")


def _upsert_user(db: Session, *, openid: str, unionid: str | None, name: str | None) -> User:
    user = db.scalar(select(User).where(User.openid == openid))
    if user is None:
        user = User(openid=openid, unionid=unionid, name=name, status="active")
        db.add(user)
    else:
        user.unionid = unionid or user.unionid
        user.name = name or user.name
        user.status = "active"
    user.last_login_at = datetime.now()
    return user


def _ensure_role(
    db: Session,
    *,
    user_id: int,
    role: str,
    campus_id: int | None,
    student_id: int | None,
    teacher_id: int | None,
) -> None:
    stored_role = role
    if role == "learner":
        stored_role = "guardian"
    role_row = db.scalar(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.campus_id == campus_id,
            UserRole.role == stored_role,
        )
    )
    if role_row is None:
        db.add(UserRole(user_id=user_id, campus_id=campus_id, role=stored_role, status="active"))
    if role == "learner" and student_id:
        relation = db.scalar(
            select(GuardianStudentRelation).where(
                GuardianStudentRelation.guardian_user_id == user_id,
                GuardianStudentRelation.student_id == student_id,
            )
        )
        if relation is None:
            db.add(GuardianStudentRelation(guardian_user_id=user_id, student_id=student_id, relation="self"))
    if role == "teacher" and teacher_id:
        teacher = db.get(Teacher, teacher_id)
        if teacher:
            teacher.user_id = user_id


def _role_options(db: Session, user: User) -> list[dict]:
    options: list[dict] = []
    for role in db.scalars(select(UserRole).where(UserRole.user_id == user.id, UserRole.status == "active")).all():
        options.append({"role": role.role, "campus_id": role.campus_id})
    for relation in db.scalars(
        select(GuardianStudentRelation).where(
            GuardianStudentRelation.guardian_user_id == user.id,
            GuardianStudentRelation.status == "active",
        )
    ).all():
        options.append({"role": "learner", "student_id": relation.student_id})
    for teacher in db.scalars(select(Teacher).where(Teacher.user_id == user.id, Teacher.status == "active")).all():
        options.append({"role": "teacher", "campus_id": teacher.campus_id, "teacher_id": teacher.id})
    return options


def _role_matches(option: dict, requested: dict) -> bool:
    if option.get("role") != requested.get("role"):
        return False
    for key in ["campus_id", "student_id", "teacher_id"]:
        if requested.get(key) is not None and option.get(key) != requested.get(key):
            return False
    return True


def _token_for_role(
    *,
    user_id: int,
    role: str,
    campus_id: int | None,
    student_id: int | None,
    teacher_id: int | None,
) -> str:
    return create_access_token(
        subject=f"user:{user_id}",
        claims={
            "role": role,
            "campus_id": campus_id,
            "student_id": student_id,
            "teacher_id": teacher_id,
        },
    )
