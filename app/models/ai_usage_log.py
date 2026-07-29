# app/models/ai_usage_log.py

import uuid
from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date_jour: Mapped[date] = mapped_column(Date, nullable=False)
    nombre_appels: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "date_jour", name="uq_ai_usage_user_date"),
    )

    def __repr__(self) -> str:
        return f"<AIUsageLog user={self.user_id} date={self.date_jour} appels={self.nombre_appels}>"