# app/models/budget.py

import enum
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BudgetPeriod(str, enum.Enum):
    HEBDOMADAIRE = "hebdomadaire"
    MENSUEL = "mensuel"


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # NULL = budget global (toutes catégories), rempli = budget spécifique
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )

    montant_limite: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    devise: Mapped[str] = mapped_column(
        String(3), ForeignKey("devises.code_devise"), nullable=False
    )
    periode: Mapped[BudgetPeriod] = mapped_column(SQLEnum(BudgetPeriod), nullable=False)
    date_debut: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="budgets")
    category: Mapped["Category | None"] = relationship()

    def __repr__(self) -> str:
        return f"<Budget montant_limite={self.montant_limite} periode={self.periode}>"