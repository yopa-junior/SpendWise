# app/schemas/expense.py

import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.expense import ExpenseSource


class ExpenseCreate(BaseModel):
    wallet_id: uuid.UUID
    category_id: uuid.UUID
    montant: Decimal = Field(gt=0)
    devise: str = Field(min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=500)
    date_depense: date
    est_recurrente: bool = False


class ExpenseUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=500)
    date_depense: date | None = None


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    category_id: uuid.UUID
    montant: Decimal
    devise: str
    description: str | None
    date_depense: date
    source: ExpenseSource
    est_recurrente: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}