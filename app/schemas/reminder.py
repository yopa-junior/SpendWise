# app/schemas/reminder.py

import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.reminder import ReminderFrequency


class ReminderCreate(BaseModel):
    category_id: uuid.UUID | None = None
    libelle: str = Field(min_length=2, max_length=150)
    frequence: ReminderFrequency
    jour_echeance: int = Field(ge=0, le=31)


class ReminderUpdate(BaseModel):
    libelle: str | None = Field(default=None, min_length=2, max_length=150)
    jour_echeance: int | None = Field(default=None, ge=0, le=31)
    actif: bool | None = None


class ReminderResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID | None
    libelle: str
    frequence: ReminderFrequency
    jour_echeance: int
    actif: bool
    derniere_notification: date | None
    created_at: datetime

    model_config = {"from_attributes": True}