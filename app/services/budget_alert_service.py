import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget_notification_log import BudgetNotificationLog
from app.models.notification import NotificationType
from app.repositories.budget_repository import BudgetRepository
from app.repositories.budget_notification_log_repository import BudgetNotificationLogRepository
from app.services.budget_service import BudgetService
from app.services.notification_service import NotificationService
from app.services.fcm_service import send_push_notification  # Ajout de l'import FCM
from app.repositories.user_repository import UserRepository   # Pour récupérer l'utilisateur


class BudgetAlertService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.budget_repo = BudgetRepository(session)
        self.log_repo = BudgetNotificationLogRepository(session)
        self.budget_service = BudgetService(session)
        self.notification_service = NotificationService(session)
        self.user_repo = UserRepository(session)  # Pour récupérer l'utilisateur

    async def check_budgets_for_category(
        self, user_id: uuid.UUID, category_id: uuid.UUID | None
    ) -> None:
        """
        Vérifie tous les budgets de l'utilisateur concernés par cette catégorie
        (y compris les budgets globaux), et notifie si un nouveau seuil est franchi.
        À appeler après chaque création de dépense.
        """
        all_budgets = await self.budget_repo.list_by_user(user_id)

        budgets_concernes = [
            b for b in all_budgets if b.category_id == category_id or b.category_id is None
        ]

        for budget in budgets_concernes:
            progress = await self.budget_service.get_progress(budget.id, user_id)

            if progress.seuil_100_atteint:
                await self._notify_if_new(budget.id, user_id, NotificationType.BUDGET_SEUIL_100, progress)
            elif progress.seuil_80_atteint:
                await self._notify_if_new(budget.id, user_id, NotificationType.BUDGET_SEUIL_80, progress)

    async def _notify_if_new(self, budget_id, user_id, seuil_type: NotificationType, progress) -> None:
        deja_notifie = await self.log_repo.already_notified(budget_id, seuil_type, progress.periode_debut)
        if deja_notifie:
            return

        pourcentage_label = "100%" if seuil_type == NotificationType.BUDGET_SEUIL_100 else "80%"
        titre = f"Budget à {pourcentage_label}"
        
        # Modification pour inclure le nom du budget
        message = (
            f"Pour le budget '{budget.nom}', tu as atteint {progress.pourcentage}% de ton budget "
            f"({progress.montant_depense} {progress.devise} sur {progress.montant_limite} {progress.devise})."
        )

        # 1. Créer la notification en base de données
        await self.notification_service.create_notification(
            user_id=user_id,
            type=seuil_type,
            titre=titre,
            message=message,
            reference_id=budget_id,
        )

        # 2. Ajouter le log pour éviter les doublons
        self.session.add(
            BudgetNotificationLog(
                id=uuid.uuid4(),
                budget_id=budget_id,
                seuil_type=seuil_type,
                periode_debut=progress.periode_debut,
                created_at=datetime.now(timezone.utc),
            )
        )
        await self.session.commit()

        # 3. Envoyer la notification push via FCM
        user = await self.user_repo.get_by_id(user_id)
        if user and user.fcm_token:
            await send_push_notification(
                session=self.session,
                user_id=user_id,
                title=titre,
                body=message,
                data={"type": seuil_type.value, "budget_id": str(budget_id)}
            )