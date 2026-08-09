# app/api/v1/wallets.py

import uuid
from fastapi import APIRouter, Depends, status, HTTPException
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
    TransferRequest,
)
from app.services.wallet_service import WalletService
from app.schemas.wallet import SavingsGoalProgress

router = APIRouter(prefix="/wallets", tags=["Wallets"])


# 🔥 Helper pour convertir les wallets en réponse
def to_wallet_response(wallet) -> dict:
    return {
        "id": str(wallet.id),
        "nom_wallet": wallet.nom_wallet,
        "type_wallet": wallet.type_wallet.value if hasattr(wallet.type_wallet, 'value') else wallet.type_wallet,
        "solde": wallet.solde,
        "devise": wallet.devise,
        "montant_cible": wallet.montant_cible,
        "date_echeance": wallet.date_echeance,
        "is_active": wallet.is_active,
        "created_at": wallet.created_at.isoformat(),
        "updated_at": wallet.updated_at.isoformat(),
    }


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    data: WalletCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    wallet = await service.create_wallet(current_user.id, data)
    return to_wallet_response(wallet)


@router.get("", response_model=list[WalletResponse])
async def list_wallets(
    active_only: bool = True,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    wallets = await service.list_wallets(current_user.id, active_only)
    return [to_wallet_response(w) for w in wallets]


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    wallet = await service.get_wallet(wallet_id, current_user.id)
    return to_wallet_response(wallet)


@router.patch("/{wallet_id}", response_model=WalletResponse)
async def update_wallet(
    wallet_id: uuid.UUID,
    data: WalletUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    wallet = await service.update_wallet(wallet_id, current_user.id, data)
    return to_wallet_response(wallet)


@router.post("/{wallet_id}/deposit", response_model=WalletResponse)
async def deposit(
    wallet_id: uuid.UUID,
    data: WalletOperationRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    wallet = await service.deposit(wallet_id, current_user.id, data.montant, data.reference)
    return to_wallet_response(wallet)


@router.post("/{wallet_id}/withdraw", response_model=WalletResponse)
async def withdraw(
    wallet_id: uuid.UUID,
    data: WalletOperationRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = WalletService(session)
    wallet = await service.withdraw(wallet_id, current_user.id, data.montant, data.reference)
    return to_wallet_response(wallet)


#  TRANSFERT
@router.post("/{wallet_id}/transfer")
async def transfer(
    wallet_id: uuid.UUID,
    data: TransferRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """
    Transférer de l'argent d'un wallet source vers un wallet destination.
    Le wallet_id dans l'URL est le wallet SOURCE.
    """
    try:
        service = WalletService(session)
        result = await service.transfer(
            source_wallet_id=wallet_id,
            destination_wallet_id=uuid.UUID(data.destination_wallet_id),
            user_id=current_user.id,
            montant=data.montant,
            reference=data.reference,
        )
        return {
            "source_wallet": to_wallet_response(result["source_wallet"]),
            "destination_wallet": to_wallet_response(result["destination_wallet"]),
            "montant_source": result["montant_source"],
            "montant_destination": result["montant_destination"],
            "devise_source": result["devise_source"],
            "devise_destination": result["devise_destination"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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