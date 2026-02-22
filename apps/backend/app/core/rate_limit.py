from collections.abc import Awaitable, Callable

from fastapi import Header, HTTPException, Request
from redis.asyncio import Redis

from app.core.config import settings


async def _consume_rate_limit(
    *,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> tuple[bool, int]:
    client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        current_count = await client.incr(key)
        if current_count == 1:
            await client.expire(key, window_seconds)
        ttl_seconds = await client.ttl(key)
    except Exception:
        # Fail open to preserve availability if Redis is unavailable.
        return True, 0
    finally:
        await client.aclose()

    return current_count <= max_requests, max(0, ttl_seconds)


def create_rate_limiter(
    *,
    key_prefix: str,
    max_requests: int | Callable[[], int],
    window_seconds: int | Callable[[], int],
) -> Callable[..., Awaitable[None]]:
    async def dependency(
        request: Request,
        x_user_id: int | None = Header(default=None),
    ) -> None:
        identity = (
            f"user:{x_user_id}"
            if x_user_id is not None
            else f"ip:{request.client.host if request.client else 'unknown'}"
        )
        resolved_max_requests = max_requests() if callable(max_requests) else max_requests
        resolved_window_seconds = window_seconds() if callable(window_seconds) else window_seconds
        rate_key = f"ratelimit:{key_prefix}:{identity}"
        allowed, retry_after = await _consume_rate_limit(
            key=rate_key,
            max_requests=resolved_max_requests,
            window_seconds=resolved_window_seconds,
        )
        if allowed:
            return
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry in {retry_after}s",
        )

    return dependency
