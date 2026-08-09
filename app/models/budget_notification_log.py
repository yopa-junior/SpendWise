# app/models/budget_notification_log.py

import uuid
from datetime import datetime, date
from sqlalchemy import DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.notification import NotificationType


class BudgetNotificationLog(Base):
    __tablename__ = "budget_notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    budget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seuil_type: Mapped[NotificationType] = mapped_column(nullable=False)
    periode_debut: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("budget_id", "seuil_type", "periode_debut", name="uq_budget_notif_period"),
    )

    def __repr__(self) -> str:
        return f"<BudgetNotificationLog budget={self.budget_id} seuil={self.seuil_type}>"