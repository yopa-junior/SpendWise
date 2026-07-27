# app/models/exchange_rate.py

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    devise_source: Mapped[str] = mapped_column(
        String(3), ForeignKey("devises.code_devise"), nullable=False, index=True
    )
    devise_cible: Mapped[str] = mapped_column(
        String(3), ForeignKey("devises.code_devise"), nullable=False, index=True
    )

    # Precision élevée : les taux de change ont souvent plusieurs décimales significatives
    taux: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)

    date_maj: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("devise_source", "devise_cible", name="uq_exchange_rate_pair"),
    )

    def __repr__(self) -> str:
        return f"<ExchangeRate {self.devise_source}->{self.devise_cible} taux={self.taux}>"