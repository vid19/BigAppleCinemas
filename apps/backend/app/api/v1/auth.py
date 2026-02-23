from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUser, get_current_user
from app.core.config import settings
from app.core.metrics import increment_metric
from app.core.rate_limit import create_rate_limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db_session
from app.models.auth_session import RefreshTokenSession
from app.models.user import User
from app.schemas.auth import (
    AuthLoginRequest,
    AuthLogoutRequest,
    AuthRefreshRequest,
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


def _to_auth_token_response(
    *,
    user: User,
    access_token: str,
    refresh_token: str,
) -> AuthTokenResponse:
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_in_seconds=settings.jwt_access_token_minutes * 60,
        refresh_expires_in_seconds=settings.jwt_refresh_token_minutes * 60,
        user=AuthUserRead.model_validate(user),
    )


async def _issue_auth_tokens(
    *,
    session: AsyncSession,
    user: User,
) -> AuthTokenResponse:
    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_in_minutes=settings.jwt_access_token_minutes,
    )
    refresh_token, refresh_expires_at = create_refresh_token(
        user_id=user.id,
        role=user.role,
        expires_in_minutes=settings.jwt_refresh_token_minutes,
    )
    session.add(
        RefreshTokenSession(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=refresh_expires_at,
        )
    )
    await session.flush()
    await _prune_refresh_sessions(
        session=session,
        user_id=user.id,
        now=datetime.now(tz=UTC),
    )
    return _to_auth_token_response(
        user=user,
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def _prune_refresh_sessions(
    *,
    session: AsyncSession,
    user_id: int,
    now: datetime,
) -> None:
    await session.execute(
        delete(RefreshTokenSession).where(
            RefreshTokenSession.user_id == user_id,
            (RefreshTokenSession.revoked_at.is_not(None))
            | (RefreshTokenSession.expires_at <= now),
        )
    )

    max_active_sessions = max(settings.auth_max_active_sessions, 1)
    active_session_ids = list(
        (
            await session.execute(
                select(RefreshTokenSession.id)
                .where(
                    RefreshTokenSession.user_id == user_id,
                    RefreshTokenSession.revoked_at.is_(None),
                    RefreshTokenSession.expires_at > now,
                )
                .order_by(
                    RefreshTokenSession.created_at.desc(),
                    RefreshTokenSession.id.desc(),
                )
            )
        ).scalars()
    )
    overflow_ids = active_session_ids[max_active_sessions:]
    if overflow_ids:
        await session.execute(
            update(RefreshTokenSession)
            .where(RefreshTokenSession.id.in_(overflow_ids))
            .values(revoked_at=now)
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
        token_response = await _issue_auth_tokens(session=session, user=user)
    return token_response


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
        increment_metric("auth_login_failure_total")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_for_update = (
        await session.execute(select(User).where(User.id == user.id).with_for_update())
    ).scalar_one()
    token_response = await _issue_auth_tokens(session=session, user=user_for_update)
    await session.commit()
    increment_metric("auth_login_success_total")
    return token_response


@router.post("/refresh")
async def refresh_tokens(
    payload: AuthRefreshRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthTokenResponse:
    token_payload = decode_refresh_token(payload.refresh_token)
    if token_payload is None:
        increment_metric("auth_refresh_failure_total")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    raw_subject = token_payload.get("sub")
    try:
        user_id = int(raw_subject)
    except (TypeError, ValueError) as exc:
        increment_metric("auth_refresh_failure_total")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    now = datetime.now(tz=UTC)
    token_hash = hash_refresh_token(payload.refresh_token)
    async with session.begin():
        await _prune_refresh_sessions(session=session, user_id=user_id, now=now)
        refresh_session = (
            await session.execute(
                select(RefreshTokenSession)
                .where(
                    RefreshTokenSession.user_id == user_id,
                    RefreshTokenSession.token_hash == token_hash,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if refresh_session is None:
            increment_metric("auth_refresh_failure_total")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not recognized",
            )
        if refresh_session.revoked_at is not None or refresh_session.expires_at <= now:
            increment_metric("auth_refresh_failure_total")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or revoked",
            )

        user = (
            await session.execute(select(User).where(User.id == user_id).with_for_update())
        ).scalar_one_or_none()
        if user is None:
            increment_metric("auth_refresh_failure_total")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        refresh_session.revoked_at = now
        await session.flush()
        token_response = await _issue_auth_tokens(session=session, user=user)
    increment_metric("auth_refresh_success_total")
    return token_response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: AuthLogoutRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    token_payload = decode_refresh_token(payload.refresh_token)
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    raw_subject = token_payload.get("sub")
    try:
        user_id = int(raw_subject)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    if current_user.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token user mismatch")

    token_hash = hash_refresh_token(payload.refresh_token)
    now = datetime.now(tz=UTC)
    async with session.begin():
        await session.execute(
            delete(RefreshTokenSession).where(
                RefreshTokenSession.user_id == user_id,
                RefreshTokenSession.token_hash == token_hash,
            )
        )
        await session.execute(
            delete(RefreshTokenSession).where(
                RefreshTokenSession.user_id == user_id,
                RefreshTokenSession.revoked_at.is_not(None),
                RefreshTokenSession.expires_at <= now,
            )
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
