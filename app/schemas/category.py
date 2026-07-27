# app/schemas/category.py

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.category import CategoryIcon, CategoryColor


# ---------- Entrée : création ----------

class CategoryCreate(BaseModel):
    nom: str = Field(min_length=2, max_length=100)
    icone: CategoryIcon
    couleur: CategoryColor


# ---------- Entrée : mise à jour ----------

class CategoryUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=100)
    icone: CategoryIcon | None = None
    couleur: CategoryColor | None = None


# ---------- Sortie ----------

class CategoryResponse(BaseModel):
    id: uuid.UUID
    nom: str
    icone: CategoryIcon
    couleur: CategoryColor
    est_par_defaut: bool
    created_at: datetime

    model_config = {"from_attributes": True}