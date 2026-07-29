# app/api/v1/reports.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Rapports"])


@router.post("/generate-my-report")
async def generate_my_report(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Déclenche manuellement la génération du résumé mensuel pour tester, sans attendre le 1er du mois."""
    service = ReportService(session)
    await service.generate_monthly_report_for_user(current_user)
    return {"message": "Résumé généré et envoyé si des dépenses existaient le mois précédent"}