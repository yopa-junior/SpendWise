import uuid
from pydantic import BaseModel
from typing import Optional, List, Dict


class CategorySuggestionRequest(BaseModel):
    description: str


class CategorySuggestionResponse(BaseModel):
    category_id: uuid.UUID | None
    category_nom: str
    confiance: float

    
class ChatRequest(BaseModel):
    question: str
    historique: Optional[List[Dict[str, str]]] = None  # <--- NOUVEAU CHAMP AJOUTÉ


class ChatResponse(BaseModel):
    reponse: str