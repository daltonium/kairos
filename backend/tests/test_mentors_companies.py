"""
backend/tests/test_mentors_companies.py
Phase 9 regression tests.
"""
import pytest

pytestmark = pytest.mark.asyncio


async def test_mentor_profile_setup_and_directory_listing(client, mentor):
    setup_resp = await client.post(
        "/api/v1/mentors/me/profile",
        headers=mentor["headers"],
        json={"domain": "AI", "experience_years": 5, "is_available": True},
    )
    assert setup_resp.status_code == 200

    list_resp = await client.get("/api/v1/mentors/", headers=mentor["headers"])
    assert list_resp.status_code == 200
    assert any(m["user_id"] == mentor["user_id"] for m in list_resp.json())


async def test_mentor_booking_blocked_when_unavailable(client, mentor, student):
    await client.post(
        "/api/v1/mentors/me/profile",
        headers=mentor["headers"],
        json={"domain": "AI", "experience_years": 3, "is_available": False},
    )
    mentors_resp = await client.get("/api/v1/mentors/", headers=student["headers"])
    mentor_id = next(m["id"] for m in mentors_resp.json() if m["user_id"] == mentor["user_id"])

    book_resp = await client.post(
        f"/api/v1/mentors/{mentor_id}/book",
        headers=student["headers"],
        json={"scheduled_at": "2026-12-01T10:00:00Z", "duration_minutes": 30},
    )
    assert book_resp.status_code == 400


async def test_mentor_dashboard_requires_mentor_profile_first(client, mentor):
    resp = await client.get("/api/v1/mentors/me/dashboard", headers=mentor["headers"])
    assert resp.status_code == 404  # no profile set up yet in this fresh mentor fixture


async def test_company_job_posting_and_student_apply(client, company, student):
    profile_resp = await client.post(
        "/api/v1/companies/me/profile",
        headers=company["headers"],
        json={"company_name": "Pytest Corp", "industry": "Tech"},
    )
    assert profile_resp.status_code == 200

    job_resp = await client.post(
        "/api/v1/companies/jobs",
        headers=company["headers"],
        json={"title": "Pytest Backend Role", "description": "FastAPI role", "budget": 40000},
    )
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    apply_resp = await client.post(f"/api/v1/companies/jobs/{job_id}/apply", headers=student["headers"])
    assert apply_resp.status_code == 201

    duplicate_resp = await client.post(f"/api/v1/companies/jobs/{job_id}/apply", headers=student["headers"])
    assert duplicate_resp.status_code == 400


async def test_non_owner_company_cannot_view_applicants(client, company, second_student):
    await client.post(
        "/api/v1/companies/me/profile",
        headers=company["headers"],
        json={"company_name": "Isolation Test Co"},
    )
    job_resp = await client.post(
        "/api/v1/companies/jobs", headers=company["headers"], json={"title": "Isolation Job"}
    )
    job_id = job_resp.json()["id"]

    # second_student registered as role="student" via the fixture, not company --
    # require_role("company") on list_applicants should reject before ownership is even checked
    resp = await client.get(f"/api/v1/companies/jobs/{job_id}/applicants", headers=second_student["headers"])
    assert resp.status_code == 403


async def test_hiring_analytics_counts(client, company, student):
    await client.post(
        "/api/v1/companies/me/profile", headers=company["headers"], json={"company_name": "Analytics Co"}
    )
    job_resp = await client.post(
        "/api/v1/companies/jobs", headers=company["headers"], json={"title": "Analytics Job"}
    )
    job_id = job_resp.json()["id"]
    await client.post(f"/api/v1/companies/jobs/{job_id}/apply", headers=student["headers"])

    analytics_resp = await client.get("/api/v1/companies/dashboard/analytics", headers=company["headers"])
    assert analytics_resp.status_code == 200
    body = analytics_resp.json()
    assert body["total_jobs"] >= 1
    assert body["total_applicants"] >= 1
