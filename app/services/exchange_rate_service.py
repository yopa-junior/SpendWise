# app/services/exchange_rate_service.py

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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