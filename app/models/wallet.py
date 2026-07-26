# app/models/wallet.py

import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class WalletType(str, enum.Enum):
    ESPECES = "especes"
    MOBILE_MONEY = "mobile_money"
    BANQUE = "banque"


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    nom_wallet: Mapped[str] = mapped_column(String(100), nullable=False)
    type_wallet: Mapped[WalletType] = mapped_column(SQLEnum(WalletType), nullable=False)

    # Numeric plutôt que Float : indispensable pour l'argent, évite les erreurs d'arrondi binaire
    solde: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)

    devise: Mapped[str] = mapped_column(
        String(3), ForeignKey("devises.code_devise"), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="wallets")
    transactions: Mapped[list["WalletTransaction"]] = relationship(
        back_populates="wallet", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Wallet {self.nom_wallet} ({self.type_wallet}) solde={self.solde}>"