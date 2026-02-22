from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUser, get_current_user
from app.core.config import settings
from app.core.rate_limit import create_rate_limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import (
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthTokenResponse,
    AuthUserRead,
)

router = APIRouter()
login_rate_limiter = create_rate_limiter(
    key_prefix="auth:login",
    max_requests=lambda: settings.rate_limit_auth_login,
    window_seconds=lambda: settings.rate_limit_auth_window_seconds,
)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: AuthRegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthTokenResponse:
    normalized_email = payload.email.strip().lower()
    async with session.begin():
        existing_user = (
            await session.execute(select(User.id).where(User.email == normalized_email))
        ).scalar_one_or_none()
        if existing_user is not None:
            raise HTTPException(status_code=409, detail="Email is already registered")

        user = User(
            email=normalized_email,
            password_hash=hash_password(payload.password),
            role="USER",
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)

    token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_in_minutes=settings.jwt_access_token_minutes,
    )
    return AuthTokenResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_access_token_minutes * 60,
        user=AuthUserRead.model_validate(user),
    )


@router.post("/login")
async def login(
    payload: AuthLoginRequest,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(login_rate_limiter),
) -> AuthTokenResponse:
    normalized_email = payload.email.strip().lower()
    user = (
        await session.execute(select(User).where(User.email == normalized_email))
    ).scalar_one_or_none()
    password_valid = False
    if user is not None:
        try:
            password_valid = verify_password(payload.password, user.password_hash)
        except Exception:
            password_valid = False

    if user is None or not password_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_in_minutes=settings.jwt_access_token_minutes,
    )
    return AuthTokenResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_access_token_minutes * 60,
        user=AuthUserRead.model_validate(user),
    )


@router.get("/me", response_model=AuthUserRead)
async def auth_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AuthUserRead:
    user = (
        await session.execute(select(User).where(User.id == current_user.user_id))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return AuthUserRead.model_validate(user)
