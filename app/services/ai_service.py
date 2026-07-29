# app/services/ai_service.py

import uuid
from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_usage_log import AIUsageLog
from app.repositories.category_repository import CategoryRepository
from app.ai.categorizer import suggest_category
from app.exceptions.ai_exceptions import AIQuotaExceededException

DAILY_LIMIT = 50  # appels IA max par utilisateur par jour, tous usages confondus


class AIService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.category_repo = CategoryRepository(session)

    async def _check_and_increment_quota(self, user_id: uuid.UUID) -> None:
        today = date.today()
        result = await self.session.execute(
            select(AIUsageLog).where(AIUsageLog.user_id == user_id, AIUsageLog.date_jour == today)
        )
        log = result.scalar_one_or_none()

        if log is None:
            log = AIUsageLog(
                user_id=user_id,
                date_jour=today,
                nombre_appels=1,
                updated_at=datetime.now(timezone.utc),
            )
            self.session.add(log)
        else:
            if log.nombre_appels >= DAILY_LIMIT:
                raise AIQuotaExceededException()
            log.nombre_appels += 1
            log.updated_at = datetime.now(timezone.utc)

        await self.session.commit()

    async def suggest_category_for_expense(
        self, user_id: uuid.UUID, description: str
    ) -> dict | None:
        await self._check_and_increment_quota(user_id)

        categories = await self.category_repo.list_for_user(user_id)
        noms_categories = [c.nom for c in categories]

        result = await suggest_category(description, noms_categories)
        if result is None:
            return None

        # Retrouve l'id réel de la catégorie suggérée pour faciliter l'usage frontend
        category_match = next((c for c in categories if c.nom == result.categorie_nom), None)

        return {
            "category_id": category_match.id if category_match else None,
            "category_nom": result.categorie_nom,
            "confiance": result.confiance,
        }