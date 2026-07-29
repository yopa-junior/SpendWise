# app/api/v1/reminders.py

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["Rappels"])


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    data: ReminderCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = ReminderService(session)
    return await service.create_reminder(current_user.id, data)


@router.get("", response_model=list[ReminderResponse])
async def list_reminders(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = ReminderService(session)
    return await service.list_reminders(current_user.id)


@router.patch("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: uuid.UUID,
    data: ReminderUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = ReminderService(session)
    return await service.update_reminder(reminder_id, current_user.id, data)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = ReminderService(session)
    await service.delete_reminder(reminder_id, current_user.id)


@router.post("/check-now")
async def check_now(
    session: AsyncSession = Depends(get_db),
):
    """Déclenche manuellement la vérification, pour tester sans attendre 7h du matin."""
    service = ReminderService(session)
    count = await service.check_and_notify_due_reminders()
    return {"message": f"{count} rappel(s) notifié(s)"}