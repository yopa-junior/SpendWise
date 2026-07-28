# app/schemas/budget.py

import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.budget import BudgetPeriod


class BudgetCreate(BaseModel):
    category_id: uuid.UUID | None = None  # None = budget global
    montant_limite: Decimal = Field(gt=0)
    devise: str = Field(min_length=3, max_length=3)
    periode: BudgetPeriod
    date_debut: date


class BudgetUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    montant_limite: Decimal | None = Field(default=None, gt=0)


class BudgetResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID | None
    montant_limite: Decimal
    devise: str
    periode: BudgetPeriod
    date_debut: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetProgress(BaseModel):
    budget_id: uuid.UUID
    montant_limite: Decimal
    montant_depense: Decimal
    pourcentage: Decimal
    devise: str
    periode_debut: date
    periode_fin: date
    seuil_80_atteint: bool
    seuil_100_atteint: bool