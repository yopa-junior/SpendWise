# app/models/category.py

import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CategoryIcon(str, enum.Enum):
    RESTAURANT = "restaurant"
    TRANSPORT = "transport"
    LOGEMENT = "logement"
    SANTE = "sante"
    EDUCATION = "education"
    LOISIRS = "loisirs"
    SHOPPING = "shopping"
    FACTURES = "factures"
    ABONNEMENT = "abonnement"
    VOYAGE = "voyage"
    CADEAU = "cadeau"
    EPARGNE = "epargne"
    FAMILLE = "famille"
    ANIMAUX = "animaux"
    SPORT = "sport"
    BEAUTE = "beaute"
    ASSURANCE = "assurance"
    IMPOTS = "impots"
    DON = "don"
    AUTRE = "autre"


class CategoryColor(str, enum.Enum):
    BLEU = "#2563eb"
    ROUGE = "#dc2626"
    VERT = "#059669"
    ORANGE = "#f59e0b"
    VIOLET = "#7c3aed"
    ROSE = "#db2777"
    JAUNE = "#eab308"
    GRIS = "#6b7280"
    CYAN = "#0891b2"
    INDIGO = "#4f46e5"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    icone: Mapped[CategoryIcon] = mapped_column(SQLEnum(CategoryIcon), nullable=False)
    couleur: Mapped[CategoryColor] = mapped_column(SQLEnum(CategoryColor), nullable=False)
    est_par_defaut: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="categories")

    __table_args__ = (
        UniqueConstraint("user_id", "nom", name="uq_category_user_nom"),
    )

    def __repr__(self) -> str:
        return f"<Category {self.nom} defaut={self.est_par_defaut}>"