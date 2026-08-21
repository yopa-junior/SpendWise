# app/services/ai_service.py

import uuid
from datetime import date, datetime, timezone
from typing import List, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_usage_log import AIUsageLog
from app.repositories.category_repository import CategoryRepository
from app.ai.categorizer import suggest_category
from app.exceptions.ai_exceptions import AIQuotaExceededException

from app.ai.chatbot import (
    detect_intent,
    formulate_response,
    answer_open_question,
    _resolve_period,
)

from app.ai.prompts import (
    FALLBACK_NON_RECONNUE,
    FALLBACK_ERREUR_IA,
)

from app.services.statistics_service import StatisticsService
from app.services.budget_service import BudgetService
from app.repositories.budget_repository import BudgetRepository


# ============================================
# CONFIGURATION
# ============================================

DAILY_LIMIT = 50


class AIService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.category_repo = CategoryRepository(session)

    # ============================================
    # QUOTA IA
    # ============================================

    async def _check_and_increment_quota(
        self,
        user_id: uuid.UUID,
    ) -> None:

        today = date.today()

        result = await self.session.execute(
            select(AIUsageLog).where(
                AIUsageLog.user_id == user_id,
                AIUsageLog.date_jour == today,
            )
        )

        log = result.scalar_one_or_none()

        # Première utilisation IA de la journée
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

    # ============================================
    # CATÉGORISATION AUTOMATIQUE DES DÉPENSES
    # ============================================

    async def suggest_category_for_expense(
        self,
        user_id: uuid.UUID,
        description: str,
    ) -> dict | None:

        await self._check_and_increment_quota(user_id)

        categories = await self.category_repo.list_for_user(user_id)

        noms_categories = [
            category.nom
            for category in categories
        ]

        result = await suggest_category(
            description,
            noms_categories,
        )

        if result is None:
            return None

        category_match = next(
            (
                category
                for category in categories
                if category.nom == result.categorie_nom
            ),
            None,
        )

        return {
            "category_id": (
                category_match.id
                if category_match
                else None
            ),
            "category_nom": result.categorie_nom,
            "confiance": result.confiance,
        }

    # ============================================
    # CHATBOT PRINCIPAL
    # ============================================

    async def ask_chatbot(
        self,
        user_id: uuid.UUID,
        question: str,
        historique: Optional[
            List[Dict[str, str]]
        ] = None,
    ) -> str:

        # ----------------------------------------
        # 1. Vérification du quota
        # ----------------------------------------

        await self._check_and_increment_quota(user_id)

        # ----------------------------------------
        # 2. Récupération des catégories utilisateur
        # ----------------------------------------

        categories = await self.category_repo.list_for_user(
            user_id
        )

        noms_categories = [
            category.nom
            for category in categories
        ]

        # ----------------------------------------
        # 3. Détection de l'intention
        # ----------------------------------------

        intent = await detect_intent(
            question,
            noms_categories,
        )

        if intent is None:
            return FALLBACK_ERREUR_IA

        # ----------------------------------------
        # 4. Questions générales
        # ----------------------------------------

        if intent.intention == "question_generale":

            return await answer_open_question(
                question=question,
                historique=historique,
            )

        # ----------------------------------------
        # 5. Questions concernant SpendWise
        # ----------------------------------------

        if intent.intention == "question_application":

            return await answer_open_question(
                question=question,
                historique=historique,
            )

        # ----------------------------------------
        # 6. Question financière non supportée
        # ----------------------------------------

        if intent.intention == "non_reconnue":

            return FALLBACK_NON_RECONNUE

        # ----------------------------------------
        # 7. Détermination de la période
        # ----------------------------------------

        stats_service = StatisticsService(
            self.session
        )

        date_debut, date_fin = _resolve_period(
            intent.periode
        )

        # ========================================
        # TOTAL DES DÉPENSES SUR UNE PÉRIODE
        # ========================================

        if intent.intention == "total_periode":

            summary = await stats_service.get_summary(
                user_id,
                date_debut,
                date_fin,
            )

            donnee = (
                f"{summary.total_periode} "
                f"{summary.devise}"
            )

            return await formulate_response(
                question=question,
                donnee=donnee,
                historique=historique,
            )

        # ========================================
        # CATÉGORIE PRINCIPALE
        # ========================================

        if intent.intention == "categorie_principale":

            summary = await stats_service.get_summary(
                user_id,
                date_debut,
                date_fin,
            )

            if summary.categorie_principale_nom is None:

                return (
                    "Tu n'as encore aucune dépense "
                    "enregistrée sur cette période."
                )

            donnee = (
                f"{summary.categorie_principale_nom}: "
                f"{summary.categorie_principale_montant} "
                f"{summary.devise}"
            )

            return await formulate_response(
                question=question,
                donnee=donnee,
                historique=historique,
            )

        # ========================================
        # TOTAL D'UNE CATÉGORIE
        # ========================================

        if intent.intention == "total_categorie_periode":

            if intent.categorie_mentionnee is None:

                return FALLBACK_NON_RECONNUE

            breakdown = (
                await stats_service.get_category_breakdown(
                    user_id,
                    date_debut,
                    date_fin,
                )
            )

            match = next(
                (
                    row
                    for row in breakdown.repartition
                    if row.category_nom.lower()
                    == intent.categorie_mentionnee.lower()
                ),
                None,
            )

            if match is None:

                return (
                    f"Tu n'as aucune dépense en "
                    f"{intent.categorie_mentionnee} "
                    f"sur cette période."
                )

            donnee = (
                f"{match.montant_total} "
                f"{breakdown.devise}"
            )

            return await formulate_response(
                question=question,
                donnee=donnee,
                historique=historique,
            )

        # ========================================
        # PROGRESSION D'UN BUDGET
        # ========================================

        if intent.intention == "progression_budget":

            budget_repo = BudgetRepository(
                self.session
            )

            budget_service = BudgetService(
                self.session
            )

            budgets = await budget_repo.list_by_user(
                user_id
            )

            # ------------------------------------
            # Budget associé à une catégorie
            # ------------------------------------

            if intent.categorie_mentionnee is not None:

                matching_category = next(
                    (
                        category
                        for category in categories
                        if category.nom.lower()
                        == intent.categorie_mentionnee.lower()
                    ),
                    None,
                )

                budget = next(
                    (
                        budget
                        for budget in budgets
                        if matching_category
                        and budget.category_id
                        == matching_category.id
                    ),
                    None,
                )

            # ------------------------------------
            # Budget général
            # ------------------------------------

            else:

                budget = next(
                    (
                        budget
                        for budget in budgets
                        if budget.category_id is None
                    ),
                    None,
                )

            if budget is None:

                return (
                    "Je ne trouve pas de budget "
                    "correspondant à ta question."
                )

            progress = await budget_service.get_progress(
                budget.id,
                user_id,
            )

            donnee = (
                f"{progress.pourcentage}% utilisé "
                f"({progress.montant_depense} "
                f"sur {progress.montant_limite} "
                f"{progress.devise})"
            )

            return await formulate_response(
                question=question,
                donnee=donnee,
                historique=historique,
            )

        # ========================================
        # ÉVOLUTION MENSUELLE
        # ========================================

        if intent.intention == "evolution_mensuelle":

            evolution = (
                await stats_service.get_monthly_evolution(
                    user_id,
                    date.today().year,
                )
            )

            donnee = (
                "Voici l'évolution de tes dépenses "
                f"sur l'année : {evolution}"
            )

            return await formulate_response(
                question=question,
                donnee=donnee,
                historique=historique,
            )

        # ========================================
        # FALLBACK FINAL
        # ========================================

        return FALLBACK_NON_RECONNUE