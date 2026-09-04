"""
backend/tests/test_gigs.py
Phase 7 regression tests -- the fullest end-to-end pipeline test,
mirroring exactly what you verified manually in Insomnia.
"""
import pytest

pytestmark = pytest.mark.asyncio


async def test_gig_requiring_unowned_skill_is_not_eligible(client, student, company):
    fake_skill_id = "00000000-0000-0000-0000-000000000000"
    create_resp = await client.post(
        "/api/v1/gigs/",
        headers=company["headers"],
        json={"title": "Needs a skill nobody has", "required_skill_ids": [fake_skill_id]},
    )
    assert create_resp.status_code == 201

    browse_resp = await client.get("/api/v1/gigs/", headers=student["headers"])
    assert browse_resp.status_code == 200
    gig_ids = [g["id"] for g in browse_resp.json()]
    assert create_resp.json()["id"] not in gig_ids


async def test_full_gig_pipeline_apply_to_completion(client, student, mentor, company):
    create_resp = await client.post(
        "/api/v1/gigs/",
        headers=company["headers"],
        json={"title": "Open gig, no skill requirement", "budget": 100, "required_skill_ids": []},
    )
    gig_id = create_resp.json()["id"]

    apply_resp = await client.post(
        f"/api/v1/gigs/{gig_id}/apply",
        headers=student["headers"],
        json={"proposal": "I can do this", "price": 90},
    )
    assert apply_resp.status_code == 201
    application_id = apply_resp.json()["id"]

    duplicate_resp = await client.post(
        f"/api/v1/gigs/{gig_id}/apply", headers=student["headers"], json={"proposal": "again"}
    )
    assert duplicate_resp.status_code == 400

    decision_resp = await client.post(
        f"/api/v1/gigs/applications/{application_id}/decision",
        headers=company["headers"],
        json={"accept": True},
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["status"] == "accepted"

    submit_resp = await client.post(
        f"/api/v1/gigs/applications/{application_id}/submit",
        headers=student["headers"],
        json={"github_url": "https://github.com/example/test", "notes": "done"},
    )
    assert submit_resp.status_code == 201
    submission_id = submit_resp.json()["id"]

    mentor_review_resp = await client.post(
        f"/api/v1/gigs/submissions/{submission_id}/mentor-review",
        headers=mentor["headers"],
        json={"rating": 5, "feedback": "good", "approve": True},
    )
    assert mentor_review_resp.status_code == 200

    client_review_resp = await client.post(
        f"/api/v1/gigs/submissions/{submission_id}/client-review",
        headers=company["headers"],
        json={"rating": 5, "feedback": "approved", "approve": True},
    )
    assert client_review_resp.status_code == 200

    browse_resp = await client.get("/api/v1/gigs/", headers=student["headers"])
    remaining_ids = [g["id"] for g in browse_resp.json()]
    assert gig_id not in remaining_ids


async def test_non_owner_cannot_view_applications(client, student, company, second_student):
    create_resp = await client.post(
        "/api/v1/gigs/", headers=company["headers"], json={"title": "Gig for isolation test"}
    )
    gig_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/gigs/{gig_id}/applications", headers=second_student["headers"])
    assert resp.status_code == 403
