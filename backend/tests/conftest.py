"""
backend/tests/conftest.py
FINAL VERSION -- replaces all earlier attempts.

Root cause of "attached to a different loop": app/db/session.py creates
the SQLAlchemy engine at MODULE IMPORT TIME, binding its connection pool
to whichever event loop exists then. pytest-asyncio then runs each test
on its own loop, so later tests get connections bound to a stale loop.

Fix: don't fight pytest-asyncio's loop scoping. Instead, give the test
suite its OWN engine using NullPool (no connection reuse across calls,
so there's nothing to get bound to a stale loop) and override FastAPI's
get_db dependency to use it. The app's production engine in db/session.py
is untouched.
"""
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
    poolclass=NullPool,  # no persistent pool -> no connection tied to a stale loop
)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def _get_test_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _get_test_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac
    await test_engine.dispose()


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