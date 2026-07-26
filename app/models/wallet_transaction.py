# app/models/wallet_transaction.py

import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TransactionType(str, enum.Enum):
    DEPOT = "depot"
    RETRAIT = "retrait"
    DEPENSE = "depense"


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type_transaction: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    montant: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    solde_apres: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<WalletTransaction {self.type_transaction} montant={self.montant}>"