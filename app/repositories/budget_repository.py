# app/repositories/budget_repository.py

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.repositories.base_repository import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self, session: AsyncSession):
        super().__init__(Budget, session)

    async def get_by_id_and_user(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> Budget | None:
        result = await self.session.execute(
            select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Budget]:
        result = await self.session.execute(
            select(Budget).where(Budget.user_id == user_id).order_by(Budget.created_at.desc())
        )
        return list(result.scalars().all())