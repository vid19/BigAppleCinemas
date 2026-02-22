from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(
    *,
    user_id: int,
    role: str,
    expires_in_minutes: int,
) -> str:
    issued_at = datetime.now(tz=UTC)
    expires_at = issued_at + timedelta(minutes=expires_in_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "token_type": "access",
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("token_type") != "access":
            return None
        return payload
    except JWTError:
        return None


def hash_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token(
    *,
    user_id: int,
    role: str,
    expires_in_minutes: int,
) -> tuple[str, datetime]:
    issued_at = datetime.now(tz=UTC)
    expires_at = issued_at + timedelta(minutes=expires_in_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "token_type": "refresh",
        "jti": uuid4().hex,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("token_type") != "refresh":
            return None
        if not payload.get("jti"):
            return None
        return payload
    except JWTError:
        return None
