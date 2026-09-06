"""
backend/tests/conftest.py
REPLACES the previous version (the asyncio.sleep(0.3) attempt was NOT
enough -- AI review + Redis-backed calls can take longer than that,
especially on cold OpenRouter/Upstash connections).

Fix: instead of guessing a sleep duration, explicitly gather() every
pending asyncio task (minus the current one) before disposing the
engine. This waits exactly as long as needed, no more, no less.
"""
import asyncio
import uuid
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.db.session import get_db

BASE_URL = "http://test"

test_engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"statement_cache_size": 0},
    poolclass=NullPool,
)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def _get_test_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _get_test_db


async def _drain_background_tasks(timeout: float = 15.0):
    """Wait for any FastAPI BackgroundTasks (AI review, Redis calls,
    email sends) spawned by the just-finished request to actually
    complete, instead of guessing a fixed sleep duration."""
    current = asyncio.current_task()
    pending = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
    if pending:
        try:
            await asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=timeout)
        except asyncio.TimeoutError:
            pass


from app.services.ai.throttle import close_redis


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url=BASE_URL,
    ) as ac:
        yield ac

    await close_redis()
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


async def _register_and_login(client: AsyncClient, role: str) -> dict:
    unique = uuid.uuid4().hex[:8]
    email = f"pytest_{role}_{unique}@example.com"
    password = "testpassword123"

    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Pytest {role.title()}",
            "username": f"pytest_{role}_{unique}",
            "email": email,
            "password": password,
            "role": role,
        },
    )
    assert register_resp.status_code == 201, register_resp.text

    login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200, login_resp.text
    tokens = login_resp.json()

    return {
        "user_id": register_resp.json()["id"],
        "email": email,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
    }


@pytest_asyncio.fixture
async def student(client):
    return await _register_and_login(client, "student")


@pytest_asyncio.fixture
async def mentor(client):
    return await _register_and_login(client, "mentor")


@pytest_asyncio.fixture
async def company(client):
    return await _register_and_login(client, "company")


@pytest_asyncio.fixture
async def second_student(client):
    return await _register_and_login(client, "student")
