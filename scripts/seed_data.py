import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.database.session import AsyncSessionLocal
from app.models.currency import Devise

DEVISES = [
    {"code_devise": "XAF", "nom": "Franc CFA (BEAC)", "symbole": "FCFA"},
    {"code_devise": "EUR", "nom": "Euro", "symbole": "€"},
    {"code_devise": "USD", "nom": "Dollar américain", "symbole": "$"},
    {"code_devise": "GBP", "nom": "Livre sterling", "symbole": "£"},
    {"code_devise": "NGN", "nom": "Naira nigérian", "symbole": "₦"},
]


async def seed_devises():
    async with AsyncSessionLocal() as session:
        for d in DEVISES:
            devise = Devise(**d)
            session.add(devise)
        await session.commit()
    print(f"{len(DEVISES)} devises insérées avec succès")


if __name__ == "__main__":
    asyncio.run(seed_devises())