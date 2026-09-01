"""
backend/app/services/ai/code_review.py
AI code/project review — uses AI_MODEL_CODE, shares the same throttle/cache
discipline and error handling proven working in roadmap.py during Phase 5.
This gets consumed by Phase 6 (Project submission -> AI evaluation).
"""
import json
from app.core.config import settings
from app.services.ai.throttle import cached_or_call
from app.services.ai.client import AIRequestFailed, RateLimitExceeded


REVIEW_PROMPT_TEMPLATE = """You are a code reviewer for a learning platform. Review this project
submission and return STRICT JSON only, no markdown fences, no commentary, exactly this shape:
{{
  "score": 75,
  "strengths": ["short string", "short string"],
  "improvements": ["short string", "short string"],
  "summary": "one paragraph plain-text summary"
}}

Project description: {description}
GitHub URL: {github_url}
"""


async def review_project(description: str, github_url: str, project_id: str) -> dict:
    cache_key = f"code_review:{project_id}"
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        description=description or "No description provided",
        github_url=github_url or "Not provided",
    )
    try:
        raw = await cached_or_call(
            cache_key,
            settings.AI_MODEL_CODE,
            [{"role": "user", "content": prompt}],
            ttl=2592000,  # 30 days — a given project's review rarely needs regenerating
            json_mode=True,
        )
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        return json.loads(cleaned)
    except RateLimitExceeded:
        return {"error": "AI quota exceeded, review will be retried later", "score": None}
    except (AIRequestFailed, json.JSONDecodeError) as e:
        return {"error": str(e), "score": None}
