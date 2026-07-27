# app/models/expense.py

import enum
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Date, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ExpenseSource(str, enum.Enum):
    MANUELLE = "manuelle"
    IA = "ia"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True
    )

    # Montant et devise ORIGINAUX saisis par l'utilisateur (avant conversion éventuelle)
    montant: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    devise: Mapped[str] = mapped_column(
        String(3), ForeignKey("devises.code_devise"), nullable=False
    )

    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    date_depense: Mapped[date] = mapped_column(Date, nullable=False)

    source: Mapped[ExpenseSource] = mapped_column(
        SQLEnum(ExpenseSource), default=ExpenseSource.MANUELLE, nullable=False
    )
    est_recurrente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="expenses")
    wallet: Mapped["Wallet"] = relationship()
    category: Mapped["Category"] = relationship()

    def __repr__(self) -> str:
        return f"<Expense montant={self.montant} {self.devise} categorie={self.category_id}>"