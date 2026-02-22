from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedUser:
    user_id: int
    role: str


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _auth_error()

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise _auth_error()

    raw_subject = payload.get("sub")
    if raw_subject is None:
        raise _auth_error()

    try:
        user_id = int(raw_subject)
    except (TypeError, ValueError) as exc:
        raise _auth_error() from exc

    role = payload.get("role")
    if not isinstance(role, str) or not role:
        raise _auth_error()
    return AuthenticatedUser(user_id=user_id, role=role)


async def get_current_user_id(current_user: AuthenticatedUser = Depends(get_current_user)) -> int:
    return current_user.user_id


async def require_admin_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
