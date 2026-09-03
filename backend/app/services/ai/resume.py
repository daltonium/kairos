"""
backend/app/services/ai/resume.py
"AI Improve" for resume sections — reuses the same cached_or_call throttle
pattern proven working in roadmap.py and code_review.py.
"""
import hashlib
from app.core.config import settings
from app.services.ai.throttle import cached_or_call
from app.services.ai.client import AIRequestFailed, RateLimitExceeded

IMPROVE_PROMPT_TEMPLATE = """Rewrite the following resume bullet point(s) to sound more
professional, action-oriented, and quantified where plausible. Keep it concise —
return ONLY the rewritten text, no preamble, no explanation, no markdown formatting.

Original text:
{text}
"""


async def improve_resume_section(section_text: str) -> str:
    content_hash = hashlib.sha256(section_text.strip().encode()).hexdigest()[:16]
    cache_key = f"resume_improve:{content_hash}"
    prompt = IMPROVE_PROMPT_TEMPLATE.format(text=section_text)
    try:
        result = await cached_or_call(
            cache_key,
            settings.AI_MODEL_REASONING,
            [{"role": "user", "content": prompt}],
            ttl=2592000,  # 30 days - same resume draft rarely needs re-improving
            json_mode=False,
        )
        return result.strip()
    except RateLimitExceeded:
        return f"[AI quota exceeded — original text unchanged]\n{section_text}"
    except AIRequestFailed as e:
        return f"[AI improve failed: {e} — original text unchanged]\n{section_text}"
