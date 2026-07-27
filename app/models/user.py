# app/models/user.py

import uuid
import enum
from sqlalchemy import Enum as SQLEnum
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class LanguePreferee(str, enum.Enum):
    FR = "fr"
    EN = "en"


class User(Base):
    __tablename__ = "users"

    # Identifiant
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Informations de base
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Préférences
    devise_preferee: Mapped[str | None] = mapped_column(
        String(3), ForeignKey("devises.code_devise"), nullable=True
    )
    langue_preferee: Mapped[LanguePreferee] = mapped_column(
        SQLEnum(LanguePreferee), default=LanguePreferee.FR, nullable=False
    )
    fuseau_horaire: Mapped[str] = mapped_column(
        String(50), default="Africa/Douala", nullable=False
    )

    # Statut du compte
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Sécurité anti brute-force
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Profil complémentaire
    photo_profil_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Horodatage
    date_creation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    email_verifications: Mapped[list["EmailVerification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    wallets: Mapped[list["Wallet"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
    
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )