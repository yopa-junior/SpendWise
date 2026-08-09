# app/services/wallet_service.py

from typing import Optional
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction, TransactionType
from app.repositories.wallet_repository import WalletRepository
from app.repositories.wallet_transaction_repository import WalletTransactionRepository
from app.schemas.wallet import WalletCreate, WalletUpdate
from app.schemas.wallet import SavingsGoalProgress, TransferRequest
from app.exceptions.wallet_exceptions import (
    WalletNotFoundException,
    WalletInactiveException,
    InsufficientBalanceException,
)
from app.exceptions.wallet_exceptions import SavingsGoalRequiresTargetException
from app.models.wallet import WalletType


class WalletService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.wallet_repo = WalletRepository(session)
        transaction_repo_cls = WalletTransactionRepository
        self.transaction_repo = transaction_repo_cls(session)

    # ---------- Création ----------

    async def create_wallet(self, user_id: uuid.UUID, data: WalletCreate) -> Wallet:
        if data.type_wallet == WalletType.EPARGNE and data.montant_cible is None:
            raise SavingsGoalRequiresTargetException()

        wallet = Wallet(
            user_id=user_id,
            nom_wallet=data.nom_wallet,
            type_wallet=data.type_wallet,
            solde=data.solde_initial,
            devise=data.devise,
            montant_cible=data.montant_cible,
            date_echeance=data.date_echeance,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        wallet = await self.wallet_repo.create(wallet)

        if data.solde_initial > 0:
            await self._record_transaction(
                wallet=wallet,
                type_transaction=TransactionType.DEPOT,
                montant=data.solde_initial,
                reference="Solde initial à la création",
            )

        return wallet

    # ---------- Lecture ----------

    async def get_wallet(self, wallet_id: uuid.UUID, user_id: uuid.UUID) -> Wallet:
        wallet = await self.wallet_repo.get_by_id_and_user(wallet_id, user_id)
        if wallet is None:
            raise WalletNotFoundException()
        return wallet

    async def list_wallets(self, user_id: uuid.UUID, active_only: bool = True) -> list[Wallet]:
        return await self.wallet_repo.list_by_user(user_id, active_only)

    # ---------- Mise à jour ----------

    async def update_wallet(
        self, wallet_id: uuid.UUID, user_id: uuid.UUID, data: WalletUpdate
    ) -> Wallet:
        wallet = await self.get_wallet(wallet_id, user_id)

        if data.nom_wallet is not None:
            wallet.nom_wallet = data.nom_wallet
        if data.is_active is not None:
            wallet.is_active = data.is_active
        if data.montant_cible is not None: 
            wallet.montant_cible = data.montant_cible
        if data.date_echeance is not None:
            wallet.date_echeance = data.date_echeance

        wallet.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(wallet)
        return wallet

    # ---------- Dépôt ----------

    async def deposit(
        self, wallet_id: uuid.UUID, user_id: uuid.UUID, montant: Decimal, reference: str | None
    ) -> Wallet:
        wallet = await self.get_wallet(wallet_id, user_id)
        self._ensure_active(wallet)

        wallet.solde += montant
        wallet.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(wallet)

        await self._record_transaction(
            wallet=wallet,
            type_transaction=TransactionType.DEPOT,
            montant=montant,
            reference=reference,
        )
        return wallet

    # ---------- Retrait ----------

    async def withdraw(
        self,
        wallet_id: uuid.UUID,
        user_id: uuid.UUID,
        montant: Decimal,
        reference: str | None,
        expense_id: uuid.UUID | None = None,
    ) -> Wallet:
        wallet = await self.get_wallet(wallet_id, user_id)
        self._ensure_active(wallet)

        if wallet.solde < montant:
            raise InsufficientBalanceException()

        wallet.solde -= montant
        wallet.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(wallet)

        await self._record_transaction(
            wallet=wallet,
            type_transaction=TransactionType.RETRAIT,
            montant=montant,
            reference=reference,
            expense_id=expense_id,
        )
        return wallet

    # ---------- TRANSFERT (NOUVEAU) ----------

    async def transfer(
        self,
        source_wallet_id: uuid.UUID,
        destination_wallet_id: uuid.UUID,
        user_id: uuid.UUID,
        montant: Decimal,
        reference: str | None = None,
    ) -> dict:
        """
        Transférer de l'argent d'un wallet source vers un wallet destination.
        """
        from app.services.exchange_rate_service import ExchangeRateService
        
        # 1. Vérifier que les wallets existent et appartiennent à l'utilisateur
        source_wallet = await self.get_wallet(source_wallet_id, user_id)
        destination_wallet = await self.get_wallet(destination_wallet_id, user_id)
        
        # 2. Vérifier que les wallets sont actifs
        self._ensure_active(source_wallet)
        self._ensure_active(destination_wallet)
        
        # 3. Vérifier que ce n'est pas le même wallet
        if source_wallet.id == destination_wallet.id:
            raise ValueError("Impossible de transférer vers le même wallet")
        
        # 4. Vérifier le montant
        if montant <= Decimal("0"):
            raise ValueError("Le montant doit être supérieur à 0")
        
        # 5. Vérifier le solde source
        if source_wallet.solde < montant:
            raise InsufficientBalanceException()
        
        # 6. Convertir le montant si les devises sont différentes
        exchange_service = ExchangeRateService(self.session)
        if source_wallet.devise != destination_wallet.devise:
            montant_converti = await exchange_service.convert(
                montant, source_wallet.devise, destination_wallet.devise
            )
        else:
            montant_converti = montant
        
        # 7. Débiter le wallet source
        source_wallet.solde -= montant
        source_wallet.updated_at = datetime.now(timezone.utc)
        
        # 8. Créer la transaction source (retrait)
        source_transaction = WalletTransaction(
            wallet_id=source_wallet.id,
            type_transaction=TransactionType.RETRAIT,
            montant=montant,
            solde_apres=source_wallet.solde,
            reference=reference or f"Virement vers {destination_wallet.nom_wallet}",
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(source_transaction)
        
        # 9. Créditer le wallet destination
        destination_wallet.solde += montant_converti
        destination_wallet.updated_at = datetime.now(timezone.utc)
        
        # 10. Créer la transaction destination (dépôt)
        destination_transaction = WalletTransaction(
            wallet_id=destination_wallet.id,
            type_transaction=TransactionType.DEPOT,
            montant=montant_converti,
            solde_apres=destination_wallet.solde,
            reference=reference or f"Virement de {source_wallet.nom_wallet}",
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(destination_transaction)
        
        # 11. Commit
        await self.session.commit()
        await self.session.refresh(source_wallet)
        await self.session.refresh(destination_wallet)
        
        return {
            "source_wallet": source_wallet,
            "destination_wallet": destination_wallet,
            "montant_source": float(montant),
            "montant_destination": float(montant_converti),
            "devise_source": source_wallet.devise,
            "devise_destination": destination_wallet.devise,
        }

    # ---------- Historique ----------

    async def get_transaction_history(
        self, wallet_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[WalletTransaction]:
        await self.get_wallet(wallet_id, user_id)
        return await self.transaction_repo.list_by_wallet(wallet_id)

    # ---------- Objectif d'épargne ----------

    async def get_savings_progress(self, wallet_id: uuid.UUID, user_id: uuid.UUID) -> SavingsGoalProgress:
        wallet = await self.get_wallet(wallet_id, user_id)

        if wallet.montant_cible is None:
            raise SavingsGoalRequiresTargetException()

        pourcentage = (wallet.solde / wallet.montant_cible * 100) if wallet.montant_cible > 0 else Decimal("0")

        return SavingsGoalProgress(
            wallet_id=wallet.id,
            solde_actuel=wallet.solde,
            montant_cible=wallet.montant_cible,
            pourcentage=pourcentage.quantize(Decimal("0.01")),
            objectif_atteint=pourcentage >= 100,
            date_echeance=wallet.date_echeance,
        )

    # ---------- Utilitaires internes ----------

    def _ensure_active(self, wallet: Wallet) -> None:
        if not wallet.is_active:
            raise WalletInactiveException()

    async def _record_transaction(
        self,
        wallet: Wallet,
        type_transaction: TransactionType,
        montant: Decimal,
        reference: str | None,
        expense_id: uuid.UUID | None = None,
    ) -> WalletTransaction:
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            type_transaction=type_transaction,
            montant=montant,
            solde_apres=wallet.solde,
            reference=reference,
            expense_id=expense_id,
            created_at=datetime.now(timezone.utc),
        )
        return await self.transaction_repo.create(transaction)