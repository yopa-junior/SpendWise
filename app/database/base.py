# app/database/base.py

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


# Force l'enregistrement de tous les modèles auprès de SQLAlchemy
# avant toute utilisation (nécessaire pour résoudre les ForeignKey/relationships)

from app.models import (  # noqa: E402, F401
    user,
    currency,
    refresh_token,
    email_verification,
    wallet,
    wallet_transaction,
    category,
    exchange_rate,
    expense,
)