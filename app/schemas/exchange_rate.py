# app/schemas/exchange_rate.py

from decimal import Decimal
from pydantic import BaseModel


class ConversionRequest(BaseModel):
    montant: Decimal
    devise_source: str
    devise_cible: str


class ConversionResponse(BaseModel):
    montant_original: Decimal
    montant_converti: Decimal
    devise_source: str
    devise_cible: str