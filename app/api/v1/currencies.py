# app/api/v1/currencies.py

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.currency import Devise
from app.schemas.currency import DeviseResponse

router = APIRouter(prefix="/devises", tags=["Devises"])


@router.get("", response_model=list[DeviseResponse])
async def list_devises(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Devise))
    return list(result.scalars().all())