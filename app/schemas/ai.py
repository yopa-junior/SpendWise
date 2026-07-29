# app/schemas/ai.py

import uuid
from pydantic import BaseModel


class CategorySuggestionRequest(BaseModel):
    description: str


class CategorySuggestionResponse(BaseModel):
    category_id: uuid.UUID | None
    category_nom: str
    confiance: float
    
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    reponse: str