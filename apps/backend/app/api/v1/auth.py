from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.rate_limit import create_rate_limiter

router = APIRouter()
login_rate_limiter = create_rate_limiter(
    key_prefix="auth:login",
    max_requests=lambda: settings.rate_limit_auth_login,
    window_seconds=lambda: settings.rate_limit_auth_window_seconds,
)


@router.post("/register")
async def register() -> dict[str, str]:
    return {"message": "register endpoint scaffold"}


@router.post("/login")
async def login(_: None = Depends(login_rate_limiter)) -> dict[str, str]:
    return {"message": "login endpoint scaffold"}
