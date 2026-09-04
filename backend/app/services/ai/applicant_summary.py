"""
backend/app/services/ai/applicant_summary.py
AI-generated applicant summaries for the company hiring portal.
Same throttle/cache/error-handling pattern as roadmap.py, code_review.py,
and resume.py -- reuses AI_MODEL_REASONING (Liquid LFM 2.5, confirmed working).
"""
from app.core.config import settings
from app.services.ai.throttle import cached_or_call
from app.services.ai.client import AIRequestFailed, RateLimitExceeded

SUMMARY_PROMPT_TEMPLATE = """You are summarizing a job applicant for a recruiter.
Write a concise 2-3 sentence professional summary based on this data. Return ONLY
the summary text, no preamble, no markdown.

Applicant name: {name}
Skill badges: {skills}
Portfolio highlights: {portfolio}
Career goal: {career_goal}
"""


async def generate_applicant_summary(
    application_id: str, name: str, skills: str, portfolio: str, career_goal: str
) -> str:
    cache_key = f"applicant_summary:{application_id}"
    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        name=name, skills=skills or "none listed",
        portfolio=portfolio or "no portfolio items yet",
        career_goal=career_goal or "not specified",
    )
    try:
        result = await cached_or_call(
            cache_key, settings.AI_MODEL_REASONING,
            [{"role": "user", "content": prompt}],
            ttl=2592000,  # cache per applicant-profile version; regenerate manually if profile changes significantly
            json_mode=False,
        )
        return result.strip()
    except RateLimitExceeded:
        return "AI summary unavailable (quota exceeded) -- review applicant profile manually."
    except AIRequestFailed as e:
        return f"AI summary unavailable ({e}) -- review applicant profile manually."
