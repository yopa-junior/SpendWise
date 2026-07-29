# app/api/v1/ai.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.schemas.ai import CategorySuggestionRequest, CategorySuggestionResponse
from app.services.ai_service import AIService
from app.exceptions.ai_exceptions import AIUnavailableException

router = APIRouter(prefix="/ai", tags=["Intelligence Artificielle"])


@router.post("/suggest-category", response_model=CategorySuggestionResponse | None)
async def suggest_category(
    data: CategorySuggestionRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = AIService(session)
    result = await service.suggest_category_for_expense(current_user.id, data.description)

    if result is None:
        return None  # IA indisponible ou incertaine : le frontend affiche la sélection manuelle

    return CategorySuggestionResponse(**result)

from app.schemas.ai import ChatRequest, ChatResponse

@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = AIService(session)
    reponse = await service.ask_chatbot(current_user.id, data.question)
    return ChatResponse(reponse=reponse)