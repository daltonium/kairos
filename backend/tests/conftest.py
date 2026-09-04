"""
backend/tests/conftest.py
Shared pytest fixtures: async HTTP client against the live app, and
helper fixtures that register+login fresh test users per role so no
test ever depends on manually-created Insomnia accounts.
"""
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

BASE_URL = "http://test"


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


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
