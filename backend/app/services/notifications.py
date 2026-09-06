"""
backend/app/services/notifications.py
In-app notification creation helper.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.marketplace import Notification


async def create_notification(db: AsyncSession, user_id: str, category: str, message: str) -> Notification:
    notification = Notification(
        id=str(uuid.uuid4()), user_id=user_id, category=category, message=message, is_read=False,
    )
    db.add(notification)
    await db.commit()
    return notification
