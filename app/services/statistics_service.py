# app/services/statistics_service.py

import uuid
import calendar
from datetime import date
from decimal import Decimal
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.expense_repository import ExpenseRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.user_repository import UserRepository
from app.services.exchange_rate_service import ExchangeRateService
from app.schemas.statistics import (
    CategoryBreakdown,
    CategoryBreakdownResponse,
    MonthlyPoint,
    MonthlyEvolutionResponse,
    StatisticsSummary,
)
from app.exceptions.expense_exceptions import NoReferenceCurrencyException


class StatisticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.expense_repo = ExpenseRepository(session)
        self.category_repo = CategoryRepository(session)
        self.user_repo = UserRepository(session)
        self.exchange_service = ExchangeRateService(session)

    async def _resolve_currency(self, user_id: uuid.UUID, devise: str | None) -> str:
        if devise is not None:
            return devise
        user = await self.user_repo.get_by_id(user_id)
        if user.devise_preferee is None:
            raise NoReferenceCurrencyException()
        return user.devise_preferee

    async def get_category_breakdown(
        self, user_id: uuid.UUID, date_debut: date, date_fin: date, devise: str | None = None
    ) -> CategoryBreakdownResponse:
        devise_ref = await self._resolve_currency(user_id, devise)

        expenses = await self.expense_repo.list_by_user(
            user_id, date_debut=date_debut, date_fin=date_fin
        )

        montants_par_categorie: dict[uuid.UUID, Decimal] = defaultdict(lambda: Decimal("0"))
        for expense in expenses:
            montant_converti = await self.exchange_service.convert(
                expense.montant, expense.devise, devise_ref
            )
            montants_par_categorie[expense.category_id] += montant_converti

        total_general = sum(montants_par_categorie.values(), Decimal("0"))

        repartition = []
        for category_id, montant in montants_par_categorie.items():
            category = await self.category_repo.get_by_id(category_id)
            pourcentage = (montant / total_general * 100) if total_general > 0 else Decimal("0")
            repartition.append(
                CategoryBreakdown(
                    category_id=category_id,
                    category_nom=category.nom,
                    category_icone=category.icone.value,
                    category_couleur=category.couleur.value,
                    montant_total=montant.quantize(Decimal("0.01")),
                    pourcentage=pourcentage.quantize(Decimal("0.01")),
                )
            )

        repartition.sort(key=lambda r: r.montant_total, reverse=True)

        return CategoryBreakdownResponse(
            devise=devise_ref,
            periode_debut=date_debut.isoformat(),
            periode_fin=date_fin.isoformat(),
            total_general=total_general.quantize(Decimal("0.01")),
            repartition=repartition,
        )

    async def get_monthly_evolution(
        self, user_id: uuid.UUID, annee: int, devise: str | None = None
    ) -> MonthlyEvolutionResponse:
        devise_ref = await self._resolve_currency(user_id, devise)

        date_debut = date(annee, 1, 1)
        date_fin = date(annee, 12, 31)

        expenses = await self.expense_repo.list_by_user(
            user_id, date_debut=date_debut, date_fin=date_fin
        )

        montants_par_mois: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for expense in expenses:
            montant_converti = await self.exchange_service.convert(
                expense.montant, expense.devise, devise_ref
            )
            mois_key = expense.date_depense.strftime("%Y-%m")
            montants_par_mois[mois_key] += montant_converti

        points = [
            MonthlyPoint(mois=f"{annee}-{str(m).zfill(2)}", montant_total=montants_par_mois.get(f"{annee}-{str(m).zfill(2)}", Decimal("0")).quantize(Decimal("0.01")))
            for m in range(1, 13)
        ]

        return MonthlyEvolutionResponse(devise=devise_ref, points=points)

    async def get_summary(
        self, user_id: uuid.UUID, date_debut: date, date_fin: date, devise: str | None = None
    ) -> StatisticsSummary:
        devise_ref = await self._resolve_currency(user_id, devise)

        # Période courante
        expenses_actuelles = await self.expense_repo.list_by_user(
            user_id, date_debut=date_debut, date_fin=date_fin
        )
        total_actuel = Decimal("0")
        montants_par_categorie: dict[uuid.UUID, Decimal] = defaultdict(lambda: Decimal("0"))
        for expense in expenses_actuelles:
            montant_converti = await self.exchange_service.convert(
                expense.montant, expense.devise, devise_ref
            )
            total_actuel += montant_converti
            montants_par_categorie[expense.category_id] += montant_converti

        # Période précédente de même durée, pour comparaison
        duree = (date_fin - date_debut).days + 1
        from datetime import timedelta
        date_debut_precedente = date_debut - timedelta(days=duree)
        date_fin_precedente = date_debut - timedelta(days=1)

        expenses_precedentes = await self.expense_repo.list_by_user(
            user_id, date_debut=date_debut_precedente, date_fin=date_fin_precedente
        )
        total_precedent = Decimal("0")
        for expense in expenses_precedentes:
            montant_converti = await self.exchange_service.convert(
                expense.montant, expense.devise, devise_ref
            )
            total_precedent += montant_converti

        evolution = (
            ((total_actuel - total_precedent) / total_precedent * 100)
            if total_precedent > 0
            else Decimal("0")
        )

        categorie_principale_nom = None
        categorie_principale_montant = None
        if montants_par_categorie:
            top_category_id = max(montants_par_categorie, key=montants_par_categorie.get)
            category = await self.category_repo.get_by_id(top_category_id)
            categorie_principale_nom = category.nom
            categorie_principale_montant = montants_par_categorie[top_category_id].quantize(Decimal("0.01"))

        return StatisticsSummary(
            devise=devise_ref,
            periode_debut=date_debut.isoformat(),
            periode_fin=date_fin.isoformat(),
            total_periode=total_actuel.quantize(Decimal("0.01")),
            total_periode_precedente=total_precedent.quantize(Decimal("0.01")),
            evolution_pourcentage=evolution.quantize(Decimal("0.01")),
            categorie_principale_nom=categorie_principale_nom,
            categorie_principale_montant=categorie_principale_montant,
        )