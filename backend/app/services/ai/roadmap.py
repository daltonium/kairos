"""
backend/app/services/ai/roadmap.py
REPLACES roadmap_service_fixed.py.
Changes:
- Smaller default weeks (4 instead of 12) to reduce output size / timeout risk
  on free-tier model infrastructure.
- One automatic retry on AIRequestFailed (timeouts are often transient).
"""
import asyncio
import json
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.ai.throttle import cached_or_call
from app.services.ai.client import RateLimitExceeded, AIRequestFailed
from app.models.learning import Roadmap, RoadmapItem


ROADMAP_PROMPT_TEMPLATE = """You are a career roadmap generator. Create a CONCISE {weeks}-week
learning roadmap for a {skill_level} learner targeting a career in {interest}.
Career goal: {career_goal}

Keep it compact: 2-3 topics per week maximum. Return STRICT JSON only, no markdown fences,
no commentary, exactly this shape:
{{
  "weeks": [
    {{
      "week_number": 1,
      "title": "string",
      "topics": [
        {{"title": "string", "description": "short string", "estimated_hours": 5, "difficulty": "beginner"}}
      ]
    }}
  ]
}}
"""


async def generate_roadmap_content(interest: str, skill_level: str, career_goal: str, weeks: int = 4) -> dict:
    cache_key = f"roadmap:content:v2:{interest}:{skill_level}:{career_goal}:{weeks}".lower().replace(" ", "_")
    prompt = ROADMAP_PROMPT_TEMPLATE.format(
        weeks=weeks, skill_level=skill_level, interest=interest, career_goal=career_goal or "not specified"
    )

    last_error = None
    for attempt in range(2):  # one retry — free-tier timeouts are often transient
        try:
            raw = await cached_or_call(
                cache_key,
                settings.AI_MODEL_REASONING,
                [{"role": "user", "content": prompt}],
                ttl=604800,
                json_mode=True,
            )
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                if cleaned.lower().startswith("json"):
                    cleaned = cleaned[4:]
            return json.loads(cleaned)
        except AIRequestFailed as e:
            last_error = e
            if attempt == 0:
                await asyncio.sleep(2)
                continue
            raise
    raise last_error


async def create_roadmap_record(
    db: AsyncSession, user_id: str, interest: str, skill_level: str, career_goal: str
) -> Roadmap:
    roadmap = Roadmap(
        id=str(uuid.uuid4()),
        user_id=user_id,
        interest=interest,
        skill_level=skill_level,
        career_goal=career_goal,
        status="generating",
    )
    db.add(roadmap)
    await db.commit()
    await db.refresh(roadmap)
    return roadmap


async def populate_roadmap_content(db: AsyncSession, roadmap_id: str, weeks: int = 4) -> None:
    result = await db.execute(select(Roadmap).where(Roadmap.id == roadmap_id))
    roadmap = result.scalar_one_or_none()
    if roadmap is None:
        return

    try:
        content = await generate_roadmap_content(
            roadmap.interest, roadmap.skill_level, roadmap.career_goal or "", weeks
        )
        roadmap.raw_ai_response = json.dumps(content)

        for week in content.get("weeks", []):
            week_number = week.get("week_number")
            for topic in week.get("topics", []):
                item = RoadmapItem(
                    id=str(uuid.uuid4()),
                    roadmap_id=roadmap.id,
                    week_number=week_number,
                    title=topic.get("title", "Untitled topic"),
                    description=topic.get("description"),
                    estimated_hours=topic.get("estimated_hours"),
                    difficulty=topic.get("difficulty"),
                )
                db.add(item)

        roadmap.status = "ready"
        await db.commit()

    except RateLimitExceeded:
        roadmap.status = "failed"
        roadmap.raw_ai_response = json.dumps({"error": "AI quota exceeded, try again later"})
        await db.commit()
    except (AIRequestFailed, json.JSONDecodeError, KeyError) as e:
        roadmap.status = "failed"
        roadmap.raw_ai_response = json.dumps({"error": str(e)})
        await db.commit()


async def get_roadmap_with_items(db: AsyncSession, roadmap_id: str, user_id: str) -> Roadmap | None:
    result = await db.execute(
        select(Roadmap).where(Roadmap.id == roadmap_id, Roadmap.user_id == user_id)
    )
    return result.scalar_one_or_none()
