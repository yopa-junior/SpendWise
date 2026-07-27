# app/repositories/expense_repository.py

import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.repositories.base_repository import BaseRepository


class ExpenseRepository(BaseRepository[Expense]):
    def __init__(self, session: AsyncSession):
        super().__init__(Expense, session)

    async def get_by_id_and_user(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> Expense | None:
        result = await self.session.execute(
            select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID | None = None,
        wallet_id: uuid.UUID | None = None,
        date_debut: date | None = None,
        date_fin: date | None = None,
    ) -> list[Expense]:
        query = select(Expense).where(Expense.user_id == user_id)

        if category_id is not None:
            query = query.where(Expense.category_id == category_id)
        if wallet_id is not None:
            query = query.where(Expense.wallet_id == wallet_id)
        if date_debut is not None:
            query = query.where(Expense.date_depense >= date_debut)
        if date_fin is not None:
            query = query.where(Expense.date_depense <= date_fin)

        query = query.order_by(Expense.date_depense.desc(), Expense.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_category(self, category_id: uuid.UUID) -> int:
        """Utile pour empêcher la suppression d'une catégorie ayant des dépenses liées."""
        result = await self.session.execute(
            select(Expense).where(Expense.category_id == category_id)
        )
        return len(result.scalars().all())