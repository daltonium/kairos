"""
backend/debug_openrouter.py
One-off diagnostic: print the RAW OpenRouter response body so we can see
exactly why 'choices' is missing. Run: python debug_openrouter.py
"""
import asyncio
import json
import httpx
from app.core.config import settings


async def main():
    payload = {
        "model": settings.AI_MODEL_REASONING,
        "messages": [{"role": "user", "content": "Reply with JSON: {\"hello\": \"world\"}"}],
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": settings.APP_URL,
                "X-Title": "Kairos",
            },
            json=payload,
        )
    print("STATUS:", resp.status_code)
    print("RAW BODY:")
    print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
