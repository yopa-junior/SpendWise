# scripts/sync_exchange_rates.py

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

import httpx

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.models.exchange_rate import ExchangeRate
from app.models.currency import Devise

API_URL = "https://open.er-api.com/v6/latest/{base}"


async def fetch_rates_for_base(base_currency: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(API_URL.format(base=base_currency))
        response.raise_for_status()
        data = response.json()
        if data.get("result") != "success":
            raise RuntimeError(f"Échec de récupération des taux pour {base_currency}: {data}")
        return data["rates"]


async def sync_exchange_rates():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Devise.code_devise))
        devises = [row[0] for row in result.all()]

        if len(devises) < 2:
            print("Il faut au moins 2 devises en base pour générer des taux de change.")
            return

        total_inserted = 0

        for devise_source in devises:
            try:
                rates = await fetch_rates_for_base(devise_source)
            except Exception as e:
                print(f"Erreur lors de la récupération des taux pour {devise_source}: {e}")
                continue

            for devise_cible in devises:
                if devise_cible == devise_source:
                    continue
                if devise_cible not in rates:
                    print(f"Taux {devise_source}->{devise_cible} indisponible, ignoré")
                    continue

                taux_value = Decimal(str(rates[devise_cible]))

                existing = await session.execute(
                    select(ExchangeRate).where(
                        ExchangeRate.devise_source == devise_source,
                        ExchangeRate.devise_cible == devise_cible,
                    )
                )
                existing_rate = existing.scalar_one_or_none()

                if existing_rate:
                    existing_rate.taux = taux_value
                    existing_rate.date_maj = datetime.now(timezone.utc)
                else:
                    session.add(
                        ExchangeRate(
                            id=uuid.uuid4(),
                            devise_source=devise_source,
                            devise_cible=devise_cible,
                            taux=taux_value,
                            date_maj=datetime.now(timezone.utc),
                        )
                    )
                total_inserted += 1

        await session.commit()
        print(f"{total_inserted} taux de change synchronisés avec succès")


if __name__ == "__main__":
    asyncio.run(sync_exchange_rates())