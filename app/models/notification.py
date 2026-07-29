# app/models/notification.py

import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class NotificationType(str, enum.Enum):
    BUDGET_SEUIL_80 = "budget_seuil_80"
    BUDGET_SEUIL_100 = "budget_seuil_100"
    RAPPEL_FACTURE = "rappel_facture"
    RESUME_MENSUEL = "resume_mensuel"
    SYSTEME = "systeme"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), nullable=False)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Référence optionnelle vers l'entité concernée (ex: id du budget), pour permettre au frontend d'y naviguer
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    lu: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification type={self.type} lu={self.lu}>"