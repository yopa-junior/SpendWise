# app/ai/schemas.py

from pydantic import BaseModel, Field


class CategorizationResult(BaseModel):
    categorie_nom: str
    confiance: float = Field(ge=0, le=1)
    
from typing import Literal

class ChatIntent(BaseModel):
    intention: Literal[
        "total_categorie_periode",
        "total_periode",
        "categorie_principale",
        "progression_budget",
        "non_reconnue",
        "hors_sujet",
    ]
    categorie_mentionnee: str | None = None
    periode: str | None = None


class ChatResponseText(BaseModel):
    reponse: str