# app/schemas/statistics.py

import uuid
from decimal import Decimal
from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    category_id: uuid.UUID
    category_nom: str
    category_icone: str
    category_couleur: str
    montant_total: Decimal
    pourcentage: Decimal


class CategoryBreakdownResponse(BaseModel):
    devise: str
    periode_debut: str
    periode_fin: str
    total_general: Decimal
    repartition: list[CategoryBreakdown]


class MonthlyPoint(BaseModel):
    mois: str  # format "2026-07"
    montant_total: Decimal


class MonthlyEvolutionResponse(BaseModel):
    devise: str
    points: list[MonthlyPoint]


class StatisticsSummary(BaseModel):
    devise: str
    periode_debut: str
    periode_fin: str
    total_periode: Decimal
    total_periode_precedente: Decimal
    evolution_pourcentage: Decimal
    categorie_principale_nom: str | None
    categorie_principale_montant: Decimal | None