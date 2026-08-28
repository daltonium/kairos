"""
backend/app/services/ai/client.py
REPLACES the earlier version.
Fix: OpenRouter sometimes wraps upstream failures (timeouts, provider errors)
in an {"error": {...}} body while still returning HTTP 200 — must check for
this explicitly, not just rely on status_code != 200.
"""
import httpx
from app.core.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class RateLimitExceeded(Exception):
    pass


class AIRequestFailed(Exception):
    pass


async def call_openrouter(model: str, messages: list[dict], json_mode: bool = False, timeout: float = 90) -> str:
    payload = {"model": model, "messages": messages}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": settings.APP_URL,
                    "X-Title": "Kairos",
                },
                json=payload,
            )
    except httpx.TimeoutException:
        raise AIRequestFailed(f"Request to OpenRouter timed out after {timeout}s (model: {model})")

    if resp.status_code == 429:
        raise RateLimitExceeded("OpenRouter rate/daily quota exceeded")
    if resp.status_code != 200:
        raise AIRequestFailed(f"OpenRouter returned HTTP {resp.status_code}: {resp.text}")

    data = resp.json()

    # OpenRouter sometimes embeds upstream failures (timeouts, provider errors)
    # inside a 200 response as {"error": {...}} instead of a real chat completion.
    if "error" in data:
        err = data["error"]
        code = err.get("code")
        message = err.get("message", "Unknown error")
        if code == 504 or "abort" in message.lower() or "timeout" in message.lower():
            raise AIRequestFailed(f"Upstream model timed out (code {code}): {message}")
        raise AIRequestFailed(f"OpenRouter error (code {code}): {message}")

    if "choices" not in data or not data["choices"]:
        raise AIRequestFailed(f"OpenRouter response missing 'choices': {data}")

    return data["choices"][0]["message"]["content"]
