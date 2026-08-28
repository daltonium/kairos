"""
backend/app/api/v1/roadmaps.py
REPLACES both the Phase 2 stub AND the earlier buggy version above.
AI Roadmap Engine endpoints — one roadmap row created, then populated async.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.learning import RoadmapItem
from app.schemas.roadmap import (
    RoadmapGenerateRequest, RoadmapResponse, RoadmapGenerateAcceptedResponse,
)
from app.services.ai.roadmap import (
    create_roadmap_record, populate_roadmap_content, get_roadmap_with_items,
)

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "roadmaps", "status": "ok"}


@router.post("/generate", response_model=RoadmapGenerateAcceptedResponse, status_code=202)
async def generate_roadmap(
    payload: RoadmapGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates the roadmap row immediately (status='generating') and returns its ID.
    The actual OpenRouter call + item population happens in a background task.
    Frontend should poll GET /roadmaps/{id} until status is 'ready' or 'failed'.
    """
    roadmap = await create_roadmap_record(
        db, current_user.id, payload.interest, payload.skill_level, payload.career_goal or ""
    )

    async def _run_in_background():
        async with AsyncSessionLocal() as bg_db:
            await populate_roadmap_content(bg_db, roadmap.id, payload.weeks)

    background_tasks.add_task(_run_in_background)

    return RoadmapGenerateAcceptedResponse(roadmap_id=roadmap.id, status="generating")


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    roadmap = await get_roadmap_with_items(db, roadmap_id, current_user.id)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    items_result = await db.execute(
        select(RoadmapItem).where(RoadmapItem.roadmap_id == roadmap.id).order_by(RoadmapItem.week_number)
    )
    items = items_result.scalars().all()

    return RoadmapResponse(
        id=roadmap.id,
        interest=roadmap.interest,
        skill_level=roadmap.skill_level,
        career_goal=roadmap.career_goal,
        status=roadmap.status,
        items=items,
    )
