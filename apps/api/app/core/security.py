from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

ACCESS_TOKEN_ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=ACCESS_TOKEN_ALGORITHM)


def decode_access_token(token: str) -> Mapping[str, Any]:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[ACCESS_TOKEN_ALGORITHM],
    )
