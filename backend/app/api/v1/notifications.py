"""
backend/app/api/v1/notifications.py
REPLACES the Phase 2 stub.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.marketplace import Notification

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "notifications", "status": "ok"}


@router.get("/")
async def list_my_notifications(
    category: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if category:
        query = query.where(Notification.category == category)
    result = await db.execute(query.order_by(Notification.created_at.desc()))
    notifications = result.scalars().all()
    return [
        {
            "id": n.id, "category": n.category, "message": n.message,
            "is_read": n.is_read, "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")

    notification.is_read = True
    await db.commit()
    return {"status": "ok"}
