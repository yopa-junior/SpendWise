# app/services/exchange_rate_service.py

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import currencies
from app.models.exchange_rate import ExchangeRate
from app.exceptions.expense_exceptions import ExchangeRateNotFoundException


class ExchangeRateService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def convert(self, montant: Decimal, devise_source: str, devise_cible: str) -> Decimal:
        """Convertit un montant d'une devise vers une autre. Retourne le montant tel quel si les devises sont identiques."""
        if devise_source == devise_cible:
            return montant

        result = await self.session.execute(
            select(ExchangeRate).where(
                ExchangeRate.devise_source == devise_source,
                ExchangeRate.devise_cible == devise_cible,
            )
        )
        rate = result.scalar_one_or_none()

        if rate is None:
            raise ExchangeRateNotFoundException(devise_source, devise_cible)

        return (montant * rate.taux).quantize(Decimal("0.01"))


    async def get_all_rates(self) -> dict:
        """Récupérer tous les taux de change disponibles"""
        # Récupérer les devises actives
        currencies = await self.session.execute(
            select(Currency).where(Currency.is_active == True)
        )
        currencies = currencies.scalars().all()
    
        rates = {}
        for currency in currencies:
            # Récupérer le taux le plus récent pour chaque devise (base XAF)
            rate = await self.session.execute(
                select(ExchangeRate)
                .where(ExchangeRate.devise_source == "XAF")
                .where(ExchangeRate.devise_cible == currency.code)
                .order_by(ExchangeRate.date_maj.desc())
                .limit(1)
            )
            rate = rate.scalar_one_or_none()
            if rate:
                rates[currency.code] = float(rate.taux)
            else:
                rates[currency.code] = 1.0 if currency.code == "XAF" else 0.0
    
        return rates