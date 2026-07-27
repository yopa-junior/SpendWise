# app/api/v1/expenses.py

import uuid
from datetime import date
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Dépenses"])


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    data: ExpenseCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = ExpenseService(session)
    return await service.create_expense(current_user.id, data)


@router.get("", response_model=list[ExpenseResponse])
async def list_expenses(
    category_id: uuid.UUID | None = None,
    wallet_id: uuid.UUID | None = None,
    date_debut: date | None = None,
    date_fin: date | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = ExpenseService(session)
    return await service.list_expenses(current_user.id, category_id, wallet_id, date_debut, date_fin)


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = ExpenseService(session)
    return await service.get_expense(expense_id, current_user.id)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = ExpenseService(session)
    return await service.update_expense(expense_id, current_user.id, data)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = ExpenseService(session)
    await service.delete_expense(expense_id, current_user.id)