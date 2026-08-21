from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.schemas.ai import (
    CategorySuggestionRequest,
    CategorySuggestionResponse,
    ChatRequest,
    ChatResponse,
)
from app.services.ai_service import AIService


router = APIRouter(
    prefix="/ai",
    tags=["Intelligence Artificielle"],
)


@router.post(
    "/suggest-category",
    response_model=CategorySuggestionResponse | None,
)
async def suggest_category(
    data: CategorySuggestionRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = AIService(session)

    result = await service.suggest_category_for_expense(
        current_user.id,
        data.description,
    )

    if result is None:
        return None

    return CategorySuggestionResponse(**result)


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    data: ChatRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = AIService(session)

    reponse = await service.ask_chatbot(
        user_id=current_user.id,
        question=data.question,
        historique=data.historique,
    )

    return ChatResponse(reponse=reponse)