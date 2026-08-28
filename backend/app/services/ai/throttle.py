"""
backend/app/services/ai/throttle.py
Redis-backed caching + daily usage counter for OpenRouter calls.
Essential given the free-tier cap (20 req/min, 50-1000 req/day).
"""
import json
from datetime import datetime, timezone

import redis.asyncio as redis_async

from app.core.config import settings
from app.services.ai.client import call_openrouter, RateLimitExceeded

_redis = redis_async.from_url(settings.REDIS_URL, decode_responses=True)

DAILY_LIMIT_WARNING_THRESHOLD = 45  # warn/soft-block before hitting the real 50/day free cap


def _seconds_until_midnight_utc() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = tomorrow.replace(day=now.day) 
    from datetime import timedelta
    tomorrow = tomorrow + timedelta(days=1)
    return int((tomorrow - now).total_seconds())


async def _increment_daily_usage() -> int:
    key = f"openrouter:usage:{datetime.now(timezone.utc).date().isoformat()}"
    count = await _redis.incr(key)
    if count == 1:
        await _redis.expire(key, _seconds_until_midnight_utc())
    return count


async def cached_or_call(
    cache_key: str,
    model: str,
    messages: list[dict],
    ttl: int = 86400,
    json_mode: bool = False,
) -> str:
    cached = await _redis.get(cache_key)
    if cached is not None:
        return cached

    usage_today = await _increment_daily_usage()
    if usage_today > DAILY_LIMIT_WARNING_THRESHOLD:
        raise RateLimitExceeded(
            f"Approaching OpenRouter free-tier daily limit ({usage_today} calls today). "
            "Try again tomorrow or after upgrading."
        )

    result = await call_openrouter(model, messages, json_mode=json_mode)
    await _redis.set(cache_key, result, ex=ttl)
    return result
