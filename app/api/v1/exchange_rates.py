# app/api/v1/exchange_rates.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.exchange_rate import ExchangeRate
from app.models.currency import Devise as Currency
from app.services.exchange_rate_service import ExchangeRateService
from app.schemas.exchange_rate import ConversionRequest, ConversionResponse

router = APIRouter(prefix="/exchange-rates", tags=["Taux de change"])


@router.post("/convert", response_model=ConversionResponse)
async def convert_amount(
    data: ConversionRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convertir un montant d'une devise à une autre"""
    service = ExchangeRateService(session)
    montant_converti = await service.convert(
        data.montant, 
        data.devise_source, 
        data.devise_cible
    )
    return ConversionResponse(
        montant_original=data.montant,
        montant_converti=montant_converti,
        devise_source=data.devise_source,
        devise_cible=data.devise_cible,
    )


@router.get("/rates")
async def get_rates(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Récupérer tous les taux de change disponibles"""
    try:
        # Récupérer toutes les devises actives
        result = await session.execute(
            select(Currency).where(Currency.is_active == True)
        )
        currencies = result.scalars().all()
        
        rates = {}
        for currency in currencies:
            # Récupérer le taux le plus récent pour chaque devise (base XAF)
            result = await session.execute(
                select(ExchangeRate)
                .where(ExchangeRate.devise_source == "XAF")
                .where(ExchangeRate.devise_cible == currency.code)
                .order_by(ExchangeRate.date_maj.desc())
                .limit(1)
            )
            rate = result.scalar_one_or_none()
            if rate:
                rates[currency.code] = float(rate.taux)
            else:
                rates[currency.code] = 1.0 if currency.code == "XAF" else 0.0
        
        return rates
    except Exception as e:
        # Fallback en cas d'erreur
        return {
            'XAF': 1.0,
            'EUR': 0.0015,
            'USD': 0.0016,
            'GBP': 0.0013,
            'NGN': 0.68,
        }