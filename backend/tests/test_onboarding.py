"""
backend/tests/test_onboarding.py
Phase 4 regression tests.
"""
import pytest

pytestmark = pytest.mark.asyncio


async def test_get_profile_auto_creates_empty_row(client, student):
    resp = await client.get("/api/v1/users/me/profile", headers=student["headers"])
    assert resp.status_code == 200
    assert resp.json()["college"] is None


async def test_update_profile_partial_fields(client, student):
    resp = await client.post(
        "/api/v1/users/me/profile",
        headers=student["headers"],
        json={"college": "Anna University", "bio": "Testing Kairos"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["college"] == "Anna University"
    assert body["bio"] == "Testing Kairos"


async def test_interests_blocked_for_non_student(client, mentor):
    resp = await client.post(
        "/api/v1/users/me/interests", headers=mentor["headers"], json={"domains": ["AI"]}
    )
    assert resp.status_code == 403


async def test_interests_roundtrip_for_student(client, student):
    post_resp = await client.post(
        "/api/v1/users/me/interests", headers=student["headers"], json={"domains": ["AI", "Cloud"]}
    )
    assert post_resp.status_code == 204

    get_resp = await client.get("/api/v1/users/me/interests", headers=student["headers"])
    assert get_resp.status_code == 200
    assert set(get_resp.json()) == {"AI", "Cloud"}


async def test_skill_assessment_saves_onto_profile(client, student):
    resp = await client.post(
        "/api/v1/users/me/skill-assessment",
        headers=student["headers"],
        json={"skill_level": "beginner", "career_goal": "Become an ML engineer"},
    )
    assert resp.status_code == 200
    assert resp.json()["skill_level"] == "beginner"
