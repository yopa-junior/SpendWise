from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
import io

from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Rapports"])


@router.post("/generate-my-report")
async def generate_my_report(
    periode: str = Query("current", description="'current' pour le mois en cours, 'previous' pour le mois précédent"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Génère le rapport PDF et le renvoie directement en téléchargement."""
    service = ReportService(session)
    pdf_buffer = await service.generate_report_pdf(current_user, periode=periode)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=rapport_{current_user.nom}_{date.today()}.pdf"
        }
    )