import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio


async def test_mentor_review_requires_mentor_role(client, student):
    fake_review = {
        "score": 80,
        "summary": "Automated test review.",
    }

    with patch(
        "app.api.v1.learning.review_project",
        new=AsyncMock(return_value=fake_review),
    ):
        submit_resp = await client.post(
            "/api/v1/learning/projects/submit",
            headers=student["headers"],
            json={"description": "for role test"},
        )

    assert submit_resp.status_code == 202

    project_id = submit_resp.json()["id"]

    response = await client.post(
        f"/api/v1/learning/projects/{project_id}/mentor-review",
        headers=student["headers"],
        json={
            "approved": True,
            "score": 90,
            "feedback": "Students cannot submit mentor reviews.",
        },
    )

    assert response.status_code == 403