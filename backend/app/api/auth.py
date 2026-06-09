from fastapi import APIRouter
from pydantic import BaseModel

from app.core.security import create_access_token

router = APIRouter()


class WechatLoginRequest(BaseModel):
    code: str


class SwitchRoleRequest(BaseModel):
    role: str
    campus_id: int | None = None
    student_id: int | None = None


@router.post("/wechat-login")
def wechat_login(payload: WechatLoginRequest) -> dict:
    token = create_access_token(subject=f"wechat:{payload.code}", claims={"role": "pending"})
    return {
        "token": token,
        "user": {"id": 0, "name": "Unbound user"},
        "roles": [],
    }


@router.post("/switch-role")
def switch_role(payload: SwitchRoleRequest) -> dict:
    token = create_access_token(
        subject="user:0",
        claims={"role": payload.role, "campus_id": payload.campus_id, "student_id": payload.student_id},
    )
    return {"token": token}

