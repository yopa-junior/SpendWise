# app/repositories/budget_notification_log_repository.py

import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget_notification_log import BudgetNotificationLog
from app.models.notification import NotificationType
from app.repositories.base_repository import BaseRepository


class BudgetNotificationLogRepository(BaseRepository[BudgetNotificationLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(BudgetNotificationLog, session)

    async def already_notified(
        self, budget_id: uuid.UUID, seuil_type: NotificationType, periode_debut: date
    ) -> bool:
        result = await self.session.execute(
            select(BudgetNotificationLog).where(
                BudgetNotificationLog.budget_id == budget_id,
                BudgetNotificationLog.seuil_type == seuil_type,
                BudgetNotificationLog.periode_debut == periode_debut,
            )
        )
        return result.scalar_one_or_none() is not None