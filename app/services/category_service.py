# app/services/category_service.py

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.exceptions.category_exceptions import (
    CategoryNotFoundException,
    CannotModifyDefaultCategoryException,
    CategoryAlreadyExistsException,
)
from app.repositories.expense_repository import ExpenseRepository
from app.exceptions.expense_exceptions import CategoryHasExpensesException


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.category_repo = CategoryRepository(session)

    # ---------- Création ----------

    async def create_category(self, user_id: uuid.UUID, data: CategoryCreate) -> Category:
        if await self.category_repo.exists_for_user(data.nom, user_id):
            raise CategoryAlreadyExistsException()

        category = Category(
            user_id=user_id,
            nom=data.nom,
            icone=data.icone,
            couleur=data.couleur,
            est_par_defaut=False,
            created_at=datetime.now(timezone.utc),
        )
        return await self.category_repo.create(category)

    # ---------- Lecture ----------

    async def list_categories(self, user_id: uuid.UUID) -> list[Category]:
        return await self.category_repo.list_for_user(user_id)

    async def get_category(self, category_id: uuid.UUID, user_id: uuid.UUID) -> Category:
        category = await self.category_repo.get_by_id_accessible(category_id, user_id)
        if category is None:
            raise CategoryNotFoundException()
        return category

    # ---------- Mise à jour ----------

    async def update_category(
        self, category_id: uuid.UUID, user_id: uuid.UUID, data: CategoryUpdate
    ) -> Category:
        category = await self.get_category(category_id, user_id)

        if category.est_par_defaut:
            raise CannotModifyDefaultCategoryException()
        
        if data.nom is not None:
            if data.nom.lower() != category.nom.lower() and await self.category_repo.exists_for_user(data.nom, user_id):
                raise CategoryAlreadyExistsException()
        category.nom = data.nom

        if data.nom is not None:
            category.nom = data.nom
        if data.icone is not None:
            category.icone = data.icone
        if data.couleur is not None:
            category.couleur = data.couleur

        await self.session.commit()
        await self.session.refresh(category)
        return category

    # ---------- Suppression ----------

    async def delete_category(self, category_id: uuid.UUID, user_id: uuid.UUID) -> None:
        category = await self.get_category(category_id, user_id)

        if category.est_par_defaut:
            raise CannotModifyDefaultCategoryException()

        await self.category_repo.delete(category)
        
    def __init__(self, session: AsyncSession):
        self.session = session
        self.category_repo = CategoryRepository(session)
        self.expense_repo = ExpenseRepository(session)
        
    async def delete_category(self, category_id: uuid.UUID, user_id: uuid.UUID) -> None:
        category = await self.get_category(category_id, user_id)

        if category.est_par_defaut:
            raise CannotModifyDefaultCategoryException()

        if await self.expense_repo.count_by_category(category_id) > 0:
            raise CategoryHasExpensesException()

        await self.category_repo.delete(category)