# tests/unit/test_budget_period.py

from datetime import date
from app.services.budget_service import compute_current_period
from app.models.budget import BudgetPeriod


def test_monthly_period_same_month():
    debut, fin = compute_current_period(
        date_debut=date(2026, 7, 1),
        periode=BudgetPeriod.MENSUEL,
        reference=date(2026, 7, 15),
    )
    assert debut == date(2026, 7, 1)
    assert fin == date(2026, 7, 31)


def test_monthly_period_advances_to_next_month():
    debut, fin = compute_current_period(
        date_debut=date(2026, 7, 1),
        periode=BudgetPeriod.MENSUEL,
        reference=date(2026, 8, 10),
    )
    assert debut == date(2026, 8, 1)
    assert fin == date(2026, 8, 31)


def test_monthly_period_handles_day_31_overflow():
    """Un budget démarré le 31 janvier doit tomber sur le 28/29 février, pas planter."""
    debut, fin = compute_current_period(
        date_debut=date(2026, 1, 31),
        periode=BudgetPeriod.MENSUEL,
        reference=date(2026, 2, 15),
    )
    assert debut == date(2026, 2, 28)  # 2026 n'est pas bissextile


def test_weekly_period():
    debut, fin = compute_current_period(
        date_debut=date(2026, 7, 1),
        periode=BudgetPeriod.HEBDOMADAIRE,
        reference=date(2026, 7, 10),
    )
    assert (fin - debut).days == 6