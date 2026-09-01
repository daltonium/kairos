"""
backend/app/api/v1/admin.py
ADD these routes to your existing admin.py stub (keep the /ping route too).
Gives visibility into today's OpenRouter usage — critical given the free-tier
daily cap. Admin-only.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
import redis.asyncio as redis_async

from app.core.config import settings
from app.core.deps import require_role
from app.models.user import User
from app.services.ai.throttle import DAILY_LIMIT_WARNING_THRESHOLD

router = APIRouter()

_redis = redis_async.from_url(settings.REDIS_URL, decode_responses=True)


@router.get("/ping")
async def ping():
    return {"router": "admin", "status": "ok"}


@router.get("/ai-usage")
async def get_ai_usage_today(current_user: User = Depends(require_role("admin"))):
    """Shows today's OpenRouter call count against the self-imposed soft cap."""
    today_key = f"openrouter:usage:{datetime.now(timezone.utc).date().isoformat()}"
    count = await _redis.get(today_key)
    count = int(count) if count else 0
    ttl_seconds = await _redis.ttl(today_key)

    return {
        "date_utc": datetime.now(timezone.utc).date().isoformat(),
        "calls_today": count,
        "soft_limit": DAILY_LIMIT_WARNING_THRESHOLD,
        "hard_limit_free_tier": 50,
        "remaining_before_soft_block": max(0, DAILY_LIMIT_WARNING_THRESHOLD - count),
        "resets_in_seconds": ttl_seconds if ttl_seconds > 0 else None,
        "models_configured": {
            "reasoning": settings.AI_MODEL_REASONING,
            "code": settings.AI_MODEL_CODE,
        },
    }
