# app/schemas/wallet.py

from decimal import Decimal
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, field_serializer


class WalletCreate(BaseModel):
    nom_wallet: str = Field(..., min_length=1, max_length=100)
    type_wallet: str
    solde_initial: Decimal = Decimal("0.00")
    devise: str
    montant_cible: Optional[Decimal] = None
    date_echeance: Optional[date] = None


class WalletUpdate(BaseModel):
    nom_wallet: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    montant_cible: Optional[Decimal] = None  
    date_echeance: Optional[date] = None    


class WalletResponse(BaseModel):
    id: str
    nom_wallet: str
    type_wallet: str
    solde: Decimal
    devise: str
    montant_cible: Optional[Decimal]
    date_echeance: Optional[date]
    is_active: bool
    created_at: str
    updated_at: str

    @field_serializer('id')
    def serialize_id(self, value):
        return str(value)


class WalletOperationRequest(BaseModel):
    montant: Decimal
    reference: Optional[str] = None


class WalletTransactionResponse(BaseModel):
    id: str
    type_transaction: str
    montant: Decimal
    solde_apres: Decimal
    reference: Optional[str]
    created_at: str

    @field_serializer('id')
    def serialize_id(self, value):
        return str(value)


# AJOUT : SCHÉMA POUR LE TRANSFERT
class TransferRequest(BaseModel):
    destination_wallet_id: str
    montant: Decimal
    reference: Optional[str] = None


class SavingsGoalProgress(BaseModel):
    wallet_id: str
    solde_actuel: Decimal
    montant_cible: Decimal
    pourcentage: Decimal
    objectif_atteint: bool
    date_echeance: Optional[date] = None