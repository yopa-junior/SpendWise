# app/services/ai_service.py

import uuid
from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_usage_log import AIUsageLog
from app.repositories.category_repository import CategoryRepository
from app.ai.categorizer import suggest_category
from app.exceptions.ai_exceptions import AIQuotaExceededException
from app.ai.chatbot import detect_intent, formulate_response, _resolve_period
from app.ai.prompts import FALLBACK_NON_RECONNUE, FALLBACK_HORS_SUJET, FALLBACK_ERREUR_IA
from app.services.statistics_service import StatisticsService
from app.services.budget_service import BudgetService
from app.repositories.budget_repository import BudgetRepository

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
        
    async def ask_chatbot(self, user_id: uuid.UUID, question: str) -> str:
        await self._check_and_increment_quota(user_id)

        categories = await self.category_repo.list_for_user(user_id)
        noms_categories = [c.nom for c in categories]

        intent = await detect_intent(question, noms_categories)
        if intent is None:
            return FALLBACK_ERREUR_IA

        if intent.intention == "hors_sujet":
            return FALLBACK_HORS_SUJET

        if intent.intention == "non_reconnue":
            return FALLBACK_NON_RECONNUE

        stats_service = StatisticsService(self.session)
        date_debut, date_fin = _resolve_period(intent.periode)

        if intent.intention == "total_periode":
            summary = await stats_service.get_summary(user_id, date_debut, date_fin)
            donnee = f"{summary.total_periode} {summary.devise}"
            return await formulate_response(question, donnee)

        if intent.intention == "categorie_principale":
            summary = await stats_service.get_summary(user_id, date_debut, date_fin)
            if summary.categorie_principale_nom is None:
                return "Tu n'as encore aucune dépense enregistrée sur cette période."
            donnee = f"{summary.categorie_principale_nom}: {summary.categorie_principale_montant} {summary.devise}"
            return await formulate_response(question, donnee)

        if intent.intention == "total_categorie_periode":
            if intent.categorie_mentionnee is None:
                return FALLBACK_NON_RECONNUE
            breakdown = await stats_service.get_category_breakdown(user_id, date_debut, date_fin)
            match = next(
                (r for r in breakdown.repartition if r.category_nom.lower() == intent.categorie_mentionnee.lower()),
                None,
            )
            if match is None:
                return f"Tu n'as aucune dépense en {intent.categorie_mentionnee} sur cette période."
            donnee = f"{match.montant_total} {breakdown.devise}"
            return await formulate_response(question, donnee)

        if intent.intention == "progression_budget":
            budget_repo = BudgetRepository(self.session)
            budget_service = BudgetService(self.session)
            budgets = await budget_repo.list_by_user(user_id)

            if intent.categorie_mentionnee is not None:
                matching_category = next(
                    (c for c in categories if c.nom.lower() == intent.categorie_mentionnee.lower()), None
                )
                budget = next(
                    (b for b in budgets if matching_category and b.category_id == matching_category.id), None
                )
            else:
                budget = next((b for b in budgets if b.category_id is None), None)

            if budget is None:
                return "Je ne trouve pas de budget correspondant à ta question."

            progress = await budget_service.get_progress(budget.id, user_id)
            donnee = f"{progress.pourcentage}% utilisé ({progress.montant_depense} sur {progress.montant_limite} {progress.devise})"
            return await formulate_response(question, donnee)

        return FALLBACK_NON_RECONNUE