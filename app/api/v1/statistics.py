# app/api/v1/statistics.py

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.schemas.statistics import (
    CategoryBreakdownResponse,
    MonthlyEvolutionResponse,
    StatisticsSummary,
)
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["Statistiques"])


@router.get("/by-category", response_model=CategoryBreakdownResponse)
async def get_category_breakdown(
    date_debut: date,
    date_fin: date,
    devise: str | None = Query(default=None, min_length=3, max_length=3),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = StatisticsService(session)
    return await service.get_category_breakdown(current_user.id, date_debut, date_fin, devise)


@router.get("/monthly-evolution", response_model=MonthlyEvolutionResponse)
async def get_monthly_evolution(
    annee: int = Query(ge=2000, le=2100),
    devise: str | None = Query(default=None, min_length=3, max_length=3),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = StatisticsService(session)
    return await service.get_monthly_evolution(current_user.id, annee, devise)


@router.get("/summary", response_model=StatisticsSummary)
async def get_summary(
    date_debut: date,
    date_fin: date,
    devise: str | None = Query(default=None, min_length=3, max_length=3),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = StatisticsService(session)
    return await service.get_summary(current_user.id, date_debut, date_fin, devise)