from datetime import UTC, datetime, timedelta
from hmac import compare_digest
import hashlib
import hmac

from jose import jwt
from jose import JWTError

from app.core.config import settings


ALGORITHM = "HS256"


def create_access_token(subject: str, claims: dict | None = None) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def verify_device_signature(secret: str, timestamp: str, body: bytes, signature: str) -> bool:
    payload = timestamp.encode("utf-8") + b"." + body
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return compare_digest(expected, signature)
