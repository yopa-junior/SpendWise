# app/repositories/reminder_repository.py

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder
from app.repositories.base_repository import BaseRepository


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self, session: AsyncSession):
        super().__init__(Reminder, session)

    async def get_by_id_and_user(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Reminder | None:
        result = await self.session.execute(
            select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Reminder]:
        result = await self.session.execute(
            select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_active(self) -> list[Reminder]:
        """Tous les rappels actifs, tous utilisateurs confondus — utilisé par la tâche planifiée."""
        result = await self.session.execute(select(Reminder).where(Reminder.actif == True))  # noqa: E712
        return list(result.scalars().all())