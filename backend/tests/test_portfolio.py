import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio


async def test_resume_ai_improve_returns_text_even_on_quota_exhaustion(client, student):
    fallback = (
        "AI quota exceeded; original text unchanged: "
        "worked on a project"
    )

    with patch(
        "app.api.v1.companies.improve_resume_section",
        new=AsyncMock(return_value=fallback),
    ):
        resp = await client.post(
            "/api/v1/companies/resume/ai-improve",
            headers=student["headers"],
            json={"section_text": "worked on a project"},
        )

    assert resp.status_code == 200
    assert resp.json()["improved_text"]