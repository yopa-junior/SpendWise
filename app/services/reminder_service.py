# app/services/reminder_service.py

import uuid
from datetime import datetime, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder, ReminderFrequency
from app.models.notification import NotificationType
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.user_repository import UserRepository
from app.services.notification_service import NotificationService
from app.notifications.email.mail import send_email
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from app.exceptions.reminder_exceptions import ReminderNotFoundException, InvalidReminderDayException
from app.exceptions.category_exceptions import CategoryNotFoundException


def _validate_jour_echeance(frequence: ReminderFrequency, jour: int) -> None:
    if frequence == ReminderFrequency.MENSUEL and not (1 <= jour <= 31):
        raise InvalidReminderDayException("mensuel")
    if frequence == ReminderFrequency.HEBDOMADAIRE and not (0 <= jour <= 6):
        raise InvalidReminderDayException("hebdomadaire")


class ReminderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.reminder_repo = ReminderRepository(session)
        self.category_repo = CategoryRepository(session)
        self.user_repo = UserRepository(session)
        self.notification_service = NotificationService(session)

    # ---------- Création ----------

    async def create_reminder(self, user_id: uuid.UUID, data: ReminderCreate) -> Reminder:
        _validate_jour_echeance(data.frequence, data.jour_echeance)

        if data.category_id is not None:
            category = await self.category_repo.get_by_id_accessible(data.category_id, user_id)
            if category is None:
                raise CategoryNotFoundException()

        reminder = Reminder(
            user_id=user_id,
            category_id=data.category_id,
            libelle=data.libelle,
            frequence=data.frequence,
            jour_echeance=data.jour_echeance,
            actif=True,
            derniere_notification=None,
            created_at=datetime.now(timezone.utc),
        )
        return await self.reminder_repo.create(reminder)

    # ---------- Lecture ----------

    async def get_reminder(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Reminder:
        reminder = await self.reminder_repo.get_by_id_and_user(reminder_id, user_id)
        if reminder is None:
            raise ReminderNotFoundException()
        return reminder

    async def list_reminders(self, user_id: uuid.UUID) -> list[Reminder]:
        return await self.reminder_repo.list_by_user(user_id)

    # ---------- Mise à jour ----------

    async def update_reminder(
        self, reminder_id: uuid.UUID, user_id: uuid.UUID, data: ReminderUpdate
    ) -> Reminder:
        reminder = await self.get_reminder(reminder_id, user_id)

        if data.libelle is not None:
            reminder.libelle = data.libelle
        if data.jour_echeance is not None:
            _validate_jour_echeance(reminder.frequence, data.jour_echeance)
            reminder.jour_echeance = data.jour_echeance
        if data.actif is not None:
            reminder.actif = data.actif

        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    # ---------- Suppression ----------

    async def delete_reminder(self, reminder_id: uuid.UUID, user_id: uuid.UUID) -> None:
        reminder = await self.get_reminder(reminder_id, user_id)
        await self.reminder_repo.delete(reminder)

    # ---------- Vérification quotidienne (appelée par la tâche planifiée) ----------

    async def check_and_notify_due_reminders(self) -> int:
        """
        Vérifie tous les rappels actifs et notifie ceux dont l'échéance est aujourd'hui,
        en évitant de renotifier deux fois le même jour.
        """
        today = date.today()
        reminders = await self.reminder_repo.list_active()
        count = 0

        for reminder in reminders:
            if reminder.derniere_notification == today:
                continue  # déjà notifié aujourd'hui

            is_due = (
                (reminder.frequence == ReminderFrequency.MENSUEL and reminder.jour_echeance == today.day)
                or (reminder.frequence == ReminderFrequency.HEBDOMADAIRE and reminder.jour_echeance == today.weekday())
            )

            if not is_due:
                continue

            try:
                await self._notify_reminder(reminder)
                reminder.derniere_notification = today
                await self.session.commit()
                count += 1
            except Exception:
                continue

        return count

    async def _notify_reminder(self, reminder: Reminder) -> None:
        user = await self.user_repo.get_by_id(reminder.user_id)

        await self.notification_service.create_notification(
            user_id=reminder.user_id,
            type=NotificationType.RAPPEL_FACTURE,
            titre=f"Rappel : {reminder.libelle}",
            message=f"N'oublie pas ta facture '{reminder.libelle}', prévue aujourd'hui.",
            reference_id=reminder.id,
        )

        await send_email(
            subject=f"Rappel SpendWise : {reminder.libelle}",
            recipients=[user.email],
            template_name="reminder_email.html",
            template_body={
                "nom": user.nom,
                "libelle": reminder.libelle,
            },
        )