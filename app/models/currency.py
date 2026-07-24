# app/models/currency.py

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Devise(Base):
    __tablename__ = "devises"

    code_devise: Mapped[str] = mapped_column(String(3), primary_key=True)  # ex: XAF, EUR, USD
    nom: Mapped[str] = mapped_column(String(50), nullable=False)
    symbole: Mapped[str] = mapped_column(String(5), nullable=False)

    def __repr__(self) -> str:
        return f"<Devise {self.code_devise}>"