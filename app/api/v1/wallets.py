# app/api/v1/wallets.py

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.schemas.wallet import (
    WalletCreate,
    WalletUpdate,
    WalletResponse,
    WalletOperationRequest,
    WalletTransactionResponse,
)
from app.services.wallet_service import WalletService
from app.schemas.wallet import SavingsGoalProgress

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    data: WalletCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    return await service.create_wallet(current_user.id, data)


@router.get("", response_model=list[WalletResponse])
async def list_wallets(
    active_only: bool = True,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    return await service.list_wallets(current_user.id, active_only)


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    return await service.get_wallet(wallet_id, current_user.id)


@router.patch("/{wallet_id}", response_model=WalletResponse)
async def update_wallet(
    wallet_id: uuid.UUID,
    data: WalletUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    return await service.update_wallet(wallet_id, current_user.id, data)


@router.post("/{wallet_id}/deposit", response_model=WalletResponse)
async def deposit(
    wallet_id: uuid.UUID,
    data: WalletOperationRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    return await service.deposit(wallet_id, current_user.id, data.montant, data.reference)


@router.post("/{wallet_id}/withdraw", response_model=WalletResponse)
async def withdraw(
    wallet_id: uuid.UUID,
    data: WalletOperationRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    return await service.withdraw(wallet_id, current_user.id, data.montant, data.reference)


@router.get("/{wallet_id}/transactions", response_model=list[WalletTransactionResponse])
async def get_transaction_history(
    wallet_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    return await service.get_transaction_history(wallet_id, current_user.id)


@router.get("/{wallet_id}/savings-progress", response_model=SavingsGoalProgress)
async def get_savings_progress(
    wallet_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    return await service.get_savings_progress(wallet_id, current_user.id)