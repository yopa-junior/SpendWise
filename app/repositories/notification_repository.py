# app/repositories/notification_repository.py

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)

    async def list_by_user(self, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.lu == False)  # noqa: E712
        query = query.order_by(Notification.date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id_and_user(self, notif_id: uuid.UUID, user_id: uuid.UUID) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(Notification.id == notif_id, Notification.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def mark_as_read(self, notification: Notification) -> None:
        notification.lu = True
        await self.session.commit()

    async def mark_all_as_read(self, user_id: uuid.UUID) -> None:
        notifications = await self.list_by_user(user_id, unread_only=True)
        for n in notifications:
            n.lu = True
        await self.session.commit()

    async def count_unread(self, user_id: uuid.UUID) -> int:
        notifications = await self.list_by_user(user_id, unread_only=True)
        return len(notifications)