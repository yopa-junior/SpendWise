# app/schemas/wallet.py

import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.wallet import WalletType
from app.models.wallet_transaction import TransactionType


# ---------- Entrée : création ----------

from datetime import date

class WalletCreate(BaseModel):
    nom_wallet: str = Field(min_length=2, max_length=100)
    type_wallet: WalletType
    solde_initial: Decimal = Field(default=Decimal("0"), ge=0)
    devise: str = Field(min_length=3, max_length=3)
    montant_cible: Decimal | None = Field(default=None, gt=0)
    date_echeance: date | None = None

# ---------- Entrée : mise à jour ----------

class WalletUpdate(BaseModel):
    nom_wallet: str | None = Field(default=None, min_length=2, max_length=100)
    is_active: bool | None = None


# ---------- Entrée : opération (dépôt/retrait) ----------

class WalletOperationRequest(BaseModel):
    montant: Decimal = Field(gt=0)
    reference: str | None = Field(default=None, max_length=255)


# ---------- Sortie : wallet ----------

class WalletResponse(BaseModel):
    id: uuid.UUID
    nom_wallet: str
    type_wallet: WalletType
    solde: Decimal
    devise: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    montant_cible: Decimal | None
    date_echeance: date | None

    model_config = {"from_attributes": True}


# ---------- Sortie : transaction ----------

class WalletTransactionResponse(BaseModel):
    id: uuid.UUID
    type_transaction: TransactionType
    montant: Decimal
    solde_apres: Decimal
    reference: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
    

class SavingsGoalProgress(BaseModel):
    wallet_id: uuid.UUID
    solde_actuel: Decimal
    montant_cible: Decimal
    pourcentage: Decimal
    objectif_atteint: bool
    date_echeance: date | None