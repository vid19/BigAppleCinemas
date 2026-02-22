import json
import logging
from json import JSONDecodeError

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_client() -> Redis:
    return Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def get_cache_json(key: str) -> dict | None:
    if not settings.cache_enabled:
        return None

    client = _build_client()
    try:
        payload = await client.get(key)
    except Exception:
        logger.warning("cache_get_failed", extra={"cache_key": key})
        return None
    finally:
        await client.aclose()

    if payload is None:
        return None

    try:
        return json.loads(payload)
    except JSONDecodeError:
        logger.warning("cache_payload_decode_failed", extra={"cache_key": key})
        return None


async def set_cache_json(key: str, payload: dict, ttl_seconds: int | None = None) -> None:
    if not settings.cache_enabled:
        return

    ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
    client = _build_client()
    try:
        await client.set(key, json.dumps(payload), ex=ttl)
    except Exception:
        logger.warning("cache_set_failed", extra={"cache_key": key})
    finally:
        await client.aclose()


async def delete_cache_prefix(prefix: str) -> None:
    if not settings.cache_enabled:
        return

    client = _build_client()
    try:
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor=cursor, match=f"{prefix}*", count=200)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        logger.warning("cache_delete_prefix_failed", extra={"cache_prefix": prefix})
    finally:
        await client.aclose()
