# scripts/seed_categories.py

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).parent.parent))

from app.database.session import AsyncSessionLocal
from app.models.category import Category, CategoryIcon, CategoryColor

CATEGORIES_PAR_DEFAUT = [
    {"nom": "Alimentation", "icone": CategoryIcon.RESTAURANT, "couleur": CategoryColor.ORANGE},
    {"nom": "Transport", "icone": CategoryIcon.TRANSPORT, "couleur": CategoryColor.BLEU},
    {"nom": "Logement", "icone": CategoryIcon.LOGEMENT, "couleur": CategoryColor.VERT},
    {"nom": "Santé", "icone": CategoryIcon.SANTE, "couleur": CategoryColor.ROUGE},
    {"nom": "Éducation", "icone": CategoryIcon.EDUCATION, "couleur": CategoryColor.INDIGO},
    {"nom": "Loisirs", "icone": CategoryIcon.LOISIRS, "couleur": CategoryColor.VIOLET},
    {"nom": "Shopping", "icone": CategoryIcon.SHOPPING, "couleur": CategoryColor.ROSE},
    {"nom": "Factures", "icone": CategoryIcon.FACTURES, "couleur": CategoryColor.JAUNE},
    {"nom": "Abonnements", "icone": CategoryIcon.ABONNEMENT, "couleur": CategoryColor.CYAN},
    {"nom": "Voyage", "icone": CategoryIcon.VOYAGE, "couleur": CategoryColor.BLEU},
    {"nom": "Cadeaux", "icone": CategoryIcon.CADEAU, "couleur": CategoryColor.ROSE},
    {"nom": "Épargne", "icone": CategoryIcon.EPARGNE, "couleur": CategoryColor.VERT},
    {"nom": "Famille", "icone": CategoryIcon.FAMILLE, "couleur": CategoryColor.ORANGE},
    {"nom": "Sport", "icone": CategoryIcon.SPORT, "couleur": CategoryColor.ROUGE},
    {"nom": "Assurance", "icone": CategoryIcon.ASSURANCE, "couleur": CategoryColor.GRIS},
    {"nom": "Impôts", "icone": CategoryIcon.IMPOTS, "couleur": CategoryColor.GRIS},
    {"nom": "Dons", "icone": CategoryIcon.DON, "couleur": CategoryColor.VIOLET},
    {"nom": "Autre", "icone": CategoryIcon.AUTRE, "couleur": CategoryColor.GRIS},
]


async def seed_categories():
    async with AsyncSessionLocal() as session:
        for c in CATEGORIES_PAR_DEFAUT:
            category = Category(
                id=uuid.uuid4(),
                user_id=None,
                nom=c["nom"],
                icone=c["icone"],
                couleur=c["couleur"],
                est_par_defaut=True,
                created_at=datetime.now(timezone.utc),
            )
            session.add(category)
        await session.commit()
    print(f"{len(CATEGORIES_PAR_DEFAUT)} catégories par défaut insérées avec succès")


if __name__ == "__main__":
    asyncio.run(seed_categories())