# app/services/budget_service.py

import uuid
import calendar
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget, BudgetPeriod
from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.services.exchange_rate_service import ExchangeRateService
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetProgress
from app.exceptions.budget_exceptions import BudgetNotFoundException
from app.exceptions.category_exceptions import CategoryNotFoundException


def _add_months(d: date, months: int) -> date:
    """Ajoute un nombre de mois à une date, en gérant les débordements de jour (ex: 31 janvier + 1 mois -> 28/29 février)."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def compute_current_period(date_debut: date, periode: BudgetPeriod, reference: date | None = None) -> tuple[date, date]:
    reference = reference or date.today()

    if periode == BudgetPeriod.HEBDOMADAIRE:
        jours_ecoules = (reference - date_debut).days
        semaines_completes = jours_ecoules // 7
        debut_periode = date_debut + timedelta_days(semaines_completes * 7)
        fin_periode = debut_periode + timedelta_days(6)
        return debut_periode, fin_periode

    # Mensuel : on compare le PREMIER JOUR de chaque mois suivant, pas le jour d'échéance lui-même
    mois_ecoules = 0
    while True:
        premier_jour_mois_suivant = _add_months(date_debut.replace(day=1), mois_ecoules + 1)
        if premier_jour_mois_suivant > reference:
            break
        mois_ecoules += 1

    debut_periode = _add_months(date_debut, mois_ecoules)
    fin_periode = _add_months(date_debut, mois_ecoules + 1)
    from datetime import timedelta
    fin_periode = fin_periode - timedelta(days=1)
    return debut_periode, fin_periode


def timedelta_days(n: int):
    from datetime import timedelta
    return timedelta(days=n)


class BudgetService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.budget_repo = BudgetRepository(session)
        self.category_repo = CategoryRepository(session)
        self.expense_repo = ExpenseRepository(session)
        self.exchange_service = ExchangeRateService(session)

    # ---------- Création ----------

    async def create_budget(self, user_id: uuid.UUID, data: BudgetCreate) -> Budget:
        if data.category_id is not None:
            category = await self.category_repo.get_by_id_accessible(data.category_id, user_id)
            if category is None:
                raise CategoryNotFoundException()

        budget = Budget(
            user_id=user_id,
            category_id=data.category_id,
            montant_limite=data.montant_limite,
            devise=data.devise,
            periode=data.periode,
            date_debut=data.date_debut,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return await self.budget_repo.create(budget)

    # ---------- Lecture ----------

    async def get_budget(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> Budget:
        budget = await self.budget_repo.get_by_id_and_user(budget_id, user_id)
        if budget is None:
            raise BudgetNotFoundException()
        return budget

    async def list_budgets(self, user_id: uuid.UUID) -> list[Budget]:
        return await self.budget_repo.list_by_user(user_id)

    # ---------- Mise à jour ----------

    async def update_budget(self, budget_id: uuid.UUID, user_id: uuid.UUID, data: BudgetUpdate) -> Budget:
        budget = await self.get_budget(budget_id, user_id)

        if data.montant_limite is not None:
            budget.montant_limite = data.montant_limite
        if data.category_id is not None:
            category = await self.category_repo.get_by_id_accessible(data.category_id, user_id)
            if category is None:
                raise CategoryNotFoundException()
            budget.category_id = data.category_id

        budget.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(budget)
        return budget

    # ---------- Suppression ----------

    async def delete_budget(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> None:
        budget = await self.get_budget(budget_id, user_id)
        await self.budget_repo.delete(budget)

    # ---------- Calcul de progression ----------

    async def get_progress(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> BudgetProgress:
        budget = await self.get_budget(budget_id, user_id)
        debut_periode, fin_periode = compute_current_period(budget.date_debut, budget.periode)

        depenses = await self.expense_repo.list_by_user(
            user_id,
            category_id=budget.category_id,  # None = toutes catégories (budget global)
            date_debut=debut_periode,
            date_fin=fin_periode,
        )

        total_depense = Decimal("0")
        for expense in depenses:
            montant_converti = await self.exchange_service.convert(
                expense.montant, expense.devise, budget.devise
            )
            total_depense += montant_converti

        pourcentage = (
            (total_depense / budget.montant_limite * 100) if budget.montant_limite > 0 else Decimal("0")
        )

        return BudgetProgress(
            budget_id=budget.id,
            montant_limite=budget.montant_limite,
            montant_depense=total_depense.quantize(Decimal("0.01")),
            pourcentage=pourcentage.quantize(Decimal("0.01")),
            devise=budget.devise,
            periode_debut=debut_periode,
            periode_fin=fin_periode,
            seuil_80_atteint=pourcentage >= 80,
            seuil_100_atteint=pourcentage >= 100,
        )