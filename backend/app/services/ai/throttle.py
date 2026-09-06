"""
Redis-backed caching and daily OpenRouter usage tracking.

Important: Redis is created lazily instead of at import time. A global
async Redis client may retain connections bound to a closed pytest event
loop, especially on Windows with the Proactor event loop.
"""
from datetime import datetime, timedelta, timezone

import redis.asyncio as redis_async

from app.core.config import settings
from app.services.ai.client import RateLimitExceeded, call_openrouter

DAILY_LIMIT_WARNING_THRESHOLD = 45

_redis_client: redis_async.Redis | None = None


def get_redis() -> redis_async.Redis:
    """Return one lazily initialized Redis client for the active process."""
    global _redis_client

    if _redis_client is None:
        _redis_client = redis_async.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            health_check_interval=30,
        )

    return _redis_client


async def close_redis() -> None:
    """Close Redis cleanly during application shutdown and test teardown."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def seconds_until_midnight_utc() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return int((tomorrow - now).total_seconds())


async def increment_daily_usage() -> int:
    redis = get_redis()
    key = f"openrouter:usage:{datetime.now(timezone.utc).date().isoformat()}"

    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, seconds_until_midnight_utc())

    return count


async def cached_or_call(
    cache_key: str,
    model: str,
    messages: list[dict],
    ttl: int = 86400,
    json_mode: bool = False,
) -> str:
    redis = get_redis()

    try:
        cached = await redis.get(cache_key)
        if cached is not None:
            return cached

        usage_today = await increment_daily_usage()
        if usage_today > DAILY_LIMIT_WARNING_THRESHOLD:
            raise RateLimitExceeded(
                f"Approaching OpenRouter free-tier daily limit: "
                f"{usage_today} calls today."
            )

        result = await call_openrouter(
            model=model,
            messages=messages,
            json_mode=json_mode,
        )

        await redis.set(cache_key, result, ex=ttl)
        return result

    except RateLimitExceeded:
        raise
    except Exception:
        # Cache/usage infrastructure must not make an AI endpoint return 500.
        # Continue with the real provider call; the caller handles provider failures.
        return await call_openrouter(
            model=model,
            messages=messages,
            json_mode=json_mode,
        )