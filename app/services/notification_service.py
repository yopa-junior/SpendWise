# app/services/notification_service.py

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.repositories.notification_repository import NotificationRepository
from app.exceptions.notification_exceptions import NotificationNotFoundException


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_repo = NotificationRepository(session)

    async def create_notification(
        self,
        user_id: uuid.UUID,
        type: NotificationType,
        titre: str,
        message: str,
        reference_id: uuid.UUID | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            titre=titre,
            message=message,
            reference_id=reference_id,
            lu=False,
            date=datetime.now(timezone.utc),
        )
        return await self.notification_repo.create(notification)

    async def list_notifications(self, user_id: uuid.UUID, unread_only: bool = False):
        return await self.notification_repo.list_by_user(user_id, unread_only)

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        return await self.notification_repo.count_unread(user_id)

    async def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
        notification = await self.notification_repo.get_by_id_and_user(notification_id, user_id)
        if notification is None:
            raise NotificationNotFoundException()
        await self.notification_repo.mark_as_read(notification)
        return notification

    async def mark_all_as_read(self, user_id: uuid.UUID) -> None:
        await self.notification_repo.mark_all_as_read(user_id)