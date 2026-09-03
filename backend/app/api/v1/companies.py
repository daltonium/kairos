"""
backend/app/api/v1/companies.py
REPLACES the Phase 2 stub -- NOTE: portfolio lives here temporarily since
there's no dedicated "portfolio" router in the original 10-router layout.
If you'd rather have a separate file, create app/api/v1/portfolio.py instead
and mount it in main.py under a new prefix -- functionally identical either way.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.models.marketplace import Portfolio, PortfolioItem
from app.schemas.portfolio import (
    PortfolioResponse, PortfolioItemUpdateRequest, ResumeGenerateRequest,
    ResumeImproveRequest, ResumeImproveResponse, ResumeResponse,
)
from app.services.portfolio import _get_or_create_portfolio
from app.services.ai.resume import improve_resume_section

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "companies", "status": "ok"}


# ---------- Portfolio ----------

@router.get("/portfolio/me", response_model=PortfolioResponse)
async def get_my_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    portfolio = await _get_or_create_portfolio(db, current_user.id)
    items_result = await db.execute(select(PortfolioItem).where(PortfolioItem.portfolio_id == portfolio.id))
    items = items_result.scalars().all()
    return PortfolioResponse(id=portfolio.id, resume_url=portfolio.resume_url, items=items)


@router.post("/portfolio/items/{item_id}", response_model=PortfolioItemUpdateRequest)
async def update_portfolio_item(
    item_id: str,
    payload: PortfolioItemUpdateRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PortfolioItem).where(PortfolioItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    portfolio_result = await db.execute(select(Portfolio).where(Portfolio.id == item.portfolio_id))
    portfolio = portfolio_result.scalar_one_or_none()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your portfolio item")

    if payload.tech_stack is not None:
        item.tech_stack = payload.tech_stack
    if payload.screenshot_urls is not None:
        import json
        item.screenshot_urls = json.dumps(payload.screenshot_urls)

    await db.commit()
    return payload


# ---------- Resume ----------

@router.post("/resume/generate", response_model=ResumeResponse)
async def generate_resume(
    payload: ResumeGenerateRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """
    Builds a plain-text resume preview from portfolio items + profile.
    PDF export is intentionally simple (client-side print-to-PDF is
    recommended per the build plan) -- this endpoint returns structured
    text content the frontend renders and prints.
    """
    portfolio = await _get_or_create_portfolio(db, current_user.id)
    items_result = await db.execute(select(PortfolioItem).where(PortfolioItem.portfolio_id == portfolio.id))
    items = items_result.scalars().all()

    lines = [f"RESUME — {current_user.full_name}", f"Email: {current_user.email}", ""]
    lines.append("PROJECTS & GIGS")
    for item in items:
        lines.append(f"- {item.title}" + (f" (rating: {item.rating})" if item.rating else ""))
        if item.description:
            lines.append(f"  {item.description}")
        if item.tech_stack:
            lines.append(f"  Tech: {item.tech_stack}")

    content_preview = "\n".join(lines)
    return ResumeResponse(resume_url=portfolio.resume_url, content_preview=content_preview)


@router.post("/resume/ai-improve", response_model=ResumeImproveResponse)
async def ai_improve_resume_section(
    payload: ResumeImproveRequest,
    current_user: User = Depends(require_role("student")),
):
    improved = await improve_resume_section(payload.section_text)
    return ResumeImproveResponse(improved_text=improved)
