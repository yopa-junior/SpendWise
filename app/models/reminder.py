# app/models/reminder.py

import enum
import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Date, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ReminderFrequency(str, enum.Enum):
    MENSUEL = "mensuel"
    HEBDOMADAIRE = "hebdomadaire"


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )

    libelle: Mapped[str] = mapped_column(String(150), nullable=False)
    frequence: Mapped[ReminderFrequency] = mapped_column(SQLEnum(ReminderFrequency), nullable=False)

    # Pour fréquence mensuelle : jour du mois (1-31). Pour hebdomadaire : jour de la semaine (0=lundi, 6=dimanche)
    jour_echeance: Mapped[int] = mapped_column(Integer, nullable=False)

    actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    derniere_notification: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="reminders")
    category: Mapped["Category | None"] = relationship()

    def __repr__(self) -> str:
        return f"<Reminder {self.libelle} jour={self.jour_echeance}>"