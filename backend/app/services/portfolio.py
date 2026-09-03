"""
backend/app/services/portfolio.py
Helper to auto-append a portfolio entry whenever a gig or project is
completed/approved. Called from gigs.py and learning.py at the approval points.
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import Portfolio, PortfolioItem


async def _get_or_create_portfolio(db: AsyncSession, user_id: str) -> Portfolio:
    result = await db.execute(select(Portfolio).where(Portfolio.user_id == user_id))
    portfolio = result.scalar_one_or_none()
    if portfolio is None:
        portfolio = Portfolio(id=str(uuid.uuid4()), user_id=user_id)
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)
    return portfolio


async def add_portfolio_item(
    db: AsyncSession,
    user_id: str,
    source_type: str,  # "gig" | "project"
    source_id: str,
    title: str,
    description: str | None = None,
    rating: float | None = None,
) -> PortfolioItem:
    portfolio = await _get_or_create_portfolio(db, user_id)

    existing = await db.execute(
        select(PortfolioItem).where(
            PortfolioItem.portfolio_id == portfolio.id,
            PortfolioItem.source_type == source_type,
            PortfolioItem.source_id == source_id,
        )
    )
    item = existing.scalar_one_or_none()
    if item is not None:
        if rating is not None:
            item.rating = rating
        await db.commit()
        await db.refresh(item)
        return item

    item = PortfolioItem(
        id=str(uuid.uuid4()),
        portfolio_id=portfolio.id,
        source_type=source_type,
        source_id=source_id,
        title=title,
        description=description,
        rating=rating,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item
