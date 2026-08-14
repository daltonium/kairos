"""
Kairos Phase 0 — connection smoke test (Windows-safe).
Fix applied: disable asyncpg prepared-statement caching, required when
using Supabase's pgbouncer pooler in transaction mode (port 6543).
Run from backend/ with venv activated:  python test_connection.py
"""
import asyncio
from app.core.config import settings


def check_env_var(name: str, value: str) -> bool:
    if not value or value.upper().startswith("YOUR_"):
        print(f"  [FAIL] {name} is empty or still a placeholder in .env -> {value!r}")
        return False
    print(f"  [OK]   {name} is set")
    return True


async def check_db():
    print("\n--- Checking Supabase (Postgres) connection ---")
    if not check_env_var("DATABASE_URL", settings.DATABASE_URL):
        return
    if not settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
        print("  [FAIL] DATABASE_URL must start with 'postgresql+asyncpg://'")
        return
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(
            settings.DATABASE_URL,
            connect_args={"statement_cache_size": 0},  # required for Supabase pgbouncer (transaction mode)
        )
        async with engine.connect() as conn:
            result = await conn.exec_driver_sql("SELECT NOW();")
            print("  [OK]   Connected. Server time:", result.fetchone()[0])
        await engine.dispose()
    except Exception as e:
        print(f"  [FAIL] Could not connect: {e}")


def check_redis():
    print("\n--- Checking Redis connection ---")
    if not check_env_var("REDIS_URL", settings.REDIS_URL):
        return
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        print("  [OK]   PING response:", r.ping())
    except Exception as e:
        print(f"  [FAIL] Could not connect: {e}")


def check_openrouter():
    print("\n--- Checking OpenRouter API ---")
    if not check_env_var("OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY):
        return
    try:
        import httpx
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": settings.APP_URL,
                "X-Title": "Kairos",
            },
            json={
                "model": settings.AI_MODEL_REASONING,
                "messages": [{"role": "user", "content": "Reply with just: pong"}],
            },
            timeout=30,
        )
        data = resp.json()
        if resp.status_code == 200:
            print("  [OK]   Model replied:", data["choices"][0]["message"]["content"])
        else:
            print(f"  [FAIL] HTTP {resp.status_code}:", data)
    except Exception as e:
        print(f"  [FAIL] Could not reach OpenRouter: {e}")


async def main():
    await check_db()
    check_redis()
    check_openrouter()
    print("\nDone. Fix any [FAIL] lines above by editing backend\\.env, then re-run.")


if __name__ == "__main__":
    asyncio.run(main())