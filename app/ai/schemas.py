# app/ai/schemas.py

from pydantic import BaseModel, Field


class CategorizationResult(BaseModel):
    categorie_nom: str
    confiance: float = Field(ge=0, le=1)