# app/repositories/category_repository.py

import uuid
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession):
        super().__init__(Category, session)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Category]:
        """Retourne les catégories par défaut ET les catégories propres à l'utilisateur."""
        result = await self.session.execute(
            select(Category)
            .where(or_(Category.est_par_defaut == True, Category.user_id == user_id))  # noqa: E712
            .order_by(Category.est_par_defaut.desc(), Category.nom)
        )
        return list(result.scalars().all())

    async def get_by_id_accessible(self, category_id: uuid.UUID, user_id: uuid.UUID) -> Category | None:
        """Récupère une catégorie si elle est par défaut OU appartient à l'utilisateur."""
        result = await self.session.execute(
            select(Category).where(
                Category.id == category_id,
                or_(Category.est_par_defaut == True, Category.user_id == user_id),  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
    
    async def exists_for_user(self, nom: str, user_id: uuid.UUID | None) -> bool:
        """Vérifie si une catégorie de ce nom existe déjà, soit par défaut, soit pour cet utilisateur."""
        result = await self.session.execute(
            select(Category).where(
                Category.nom.ilike(nom),
                or_(Category.est_par_defaut == True, Category.user_id == user_id),  # noqa: E712
            )
        )
        return result.scalar_one_or_none() is not None