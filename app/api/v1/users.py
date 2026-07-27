# app/api/v1/users.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["Utilisateurs"])


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    data: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_repo = UserRepository(session)
    updated_user = await user_repo.update(
        current_user,
        nom=data.nom,
        devise_preferee=data.devise_preferee,
        langue_preferee=data.langue_preferee,
        telephone=data.telephone,
        fuseau_horaire=data.fuseau_horaire,
    )
    return updated_user