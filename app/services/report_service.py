# app/services/report_service.py

import uuid
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.notification import NotificationType
from app.services.statistics_service import StatisticsService
from app.services.notification_service import NotificationService
from app.notifications.email.mail import send_email


def _previous_month_range(reference: date | None = None) -> tuple[date, date]:
    """Calcule le premier et dernier jour du mois précédent la date de référence."""
    reference = reference or date.today()
    premier_jour_mois_actuel = reference.replace(day=1)
    dernier_jour_mois_precedent = premier_jour_mois_actuel - timedelta(days=1)
    premier_jour_mois_precedent = dernier_jour_mois_precedent.replace(day=1)
    return premier_jour_mois_precedent, dernier_jour_mois_precedent


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.statistics_service = StatisticsService(session)
        self.notification_service = NotificationService(session)

    async def generate_monthly_report_for_user(self, user: User) -> None:
        """Génère et envoie le résumé mensuel pour un utilisateur donné."""
        date_debut, date_fin = _previous_month_range()

        try:
            summary = await self.statistics_service.get_summary(user.id, date_debut, date_fin)
        except Exception:
            # Ex: aucune devise préférée définie -> on ignore silencieusement cet utilisateur
            return

        # Aucune dépense sur le mois : pas la peine d'envoyer un résumé vide
        if summary.total_periode == 0:
            return

        mois_nom = date_debut.strftime("%B %Y")

        # Notification in-app
        message = (
            f"Résumé de {mois_nom} : {summary.total_periode} {summary.devise} dépensés"
            + (f", principalement en {summary.categorie_principale_nom}." if summary.categorie_principale_nom else ".")
        )
        await self.notification_service.create_notification(
            user_id=user.id,
            type=NotificationType.RESUME_MENSUEL,
            titre=f"Ton résumé de {mois_nom}",
            message=message,
        )

        # Email
        evolution_signe = "+" if summary.evolution_pourcentage >= 0 else ""
        await send_email(
            subject=f"Ton résumé SpendWise de {mois_nom}",
            recipients=[user.email],
            template_name="monthly_report.html",
            template_body={
                "nom": user.nom,
                "mois": mois_nom,
                "total_depense": str(summary.total_periode),
                "devise": summary.devise,
                "categorie_principale": summary.categorie_principale_nom or "Aucune",
                "evolution_pourcentage": f"{evolution_signe}{summary.evolution_pourcentage}",
            },
        )

    async def generate_monthly_reports_for_all_users(self) -> int:
        """Boucle sur tous les utilisateurs actifs et vérifiés, génère leur résumé mensuel."""
        result = await self.session.execute(
            select(User).where(User.is_active == True, User.is_verified == True)  # noqa: E712
        )
        users = list(result.scalars().all())

        count = 0
        for user in users:
            try:
                await self.generate_monthly_report_for_user(user)
                count += 1
            except Exception:
                # Un échec sur un utilisateur (ex: email invalide) ne doit jamais bloquer les autres
                continue

        return count