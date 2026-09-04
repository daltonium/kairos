"""
backend/tests/test_auth.py
Phase 3 regression tests.
"""
import pytest

pytestmark = pytest.mark.asyncio


async def test_register_creates_user_without_leaking_password(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Auth Test",
            "username": f"authtest_{id(client)}",
            "email": f"authtest_{id(client)}@example.com",
            "password": "supersecret123",
            "role": "student",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "hashed_password" not in body
    assert "password" not in body
    assert body["role"] == "student"


async def test_login_wrong_password_returns_401(client, student):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": student["email"], "password": "wrongpassword"}
    )
    assert resp.status_code == 401


async def test_login_correct_password_returns_tokens(client, student):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": student["email"], "password": "testpassword123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_refresh_issues_new_token_pair(client, student):
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": student["refresh_token"]})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_protected_route_requires_auth(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_protected_route_works_with_valid_token(client, student):
    resp = await client.get("/api/v1/users/me", headers=student["headers"])
    assert resp.status_code == 200
    assert resp.json()["email"] == student["email"]
