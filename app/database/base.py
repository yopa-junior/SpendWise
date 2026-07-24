# app/database/base.py

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


# Force l'enregistrement de tous les modèles auprès de SQLAlchemy
# avant toute utilisation (nécessaire pour résoudre les ForeignKey/relationships)
from app.models import user, currency, refresh_token  # noqa: E402, F401