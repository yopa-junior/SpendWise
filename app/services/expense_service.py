# app/services/expense_service.py

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense, ExpenseSource
from app.models.wallet_transaction import TransactionType
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.category_repository import CategoryRepository
from app.services.wallet_service import WalletService
from app.services.exchange_rate_service import ExchangeRateService
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.exceptions.expense_exceptions import ExpenseNotFoundException
from app.exceptions.category_exceptions import CategoryNotFoundException


class ExpenseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.expense_repo = ExpenseRepository(session)
        self.category_repo = CategoryRepository(session)
        self.wallet_service = WalletService(session)
        self.exchange_service = ExchangeRateService(session)

    # ---------- Création ----------

    async def create_expense(self, user_id: uuid.UUID, data: ExpenseCreate) -> Expense:
        # Vérifie que le wallet appartient bien à l'utilisateur (lève 404 sinon)
        wallet = await self.wallet_service.get_wallet(data.wallet_id, user_id)

        # Vérifie que la catégorie est accessible (par défaut ou propre à l'utilisateur)
        category = await self.category_repo.get_by_id_accessible(data.category_id, user_id)
        if category is None:
            raise CategoryNotFoundException()

        # Convertit le montant vers la devise du wallet si nécessaire
        montant_wallet = await self.exchange_service.convert(
            data.montant, data.devise, wallet.devise
        )

        # Crée d'abord la dépense (avec le montant ORIGINAL, dans la devise saisie)
        expense = Expense(
            user_id=user_id,
            wallet_id=data.wallet_id,
            category_id=data.category_id,
            montant=data.montant,
            devise=data.devise,
            description=data.description,
            date_depense=data.date_depense,
            source=ExpenseSource.MANUELLE,
            est_recurrente=data.est_recurrente,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        expense = await self.expense_repo.create(expense)

        # Débite le wallet du montant converti, et trace la transaction avec le lien vers la dépense
        await self.wallet_service.withdraw(
            wallet_id=data.wallet_id,
            user_id=user_id,
            montant=montant_wallet,
            reference=f"Dépense: {data.description or category.nom}",
            expense_id=expense.id,
        )

        return expense

    # ---------- Lecture ----------

    async def get_expense(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> Expense:
        expense = await self.expense_repo.get_by_id_and_user(expense_id, user_id)
        if expense is None:
            raise ExpenseNotFoundException()
        return expense

    async def list_expenses(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID | None = None,
        wallet_id: uuid.UUID | None = None,
        date_debut: date | None = None,
        date_fin: date | None = None,
    ) -> list[Expense]:
        return await self.expense_repo.list_by_user(
            user_id, category_id, wallet_id, date_debut, date_fin
        )

    # ---------- Mise à jour (métadonnées seulement) ----------

    async def update_expense(
        self, expense_id: uuid.UUID, user_id: uuid.UUID, data: ExpenseUpdate
    ) -> Expense:
        expense = await self.get_expense(expense_id, user_id)

        if data.category_id is not None:
            category = await self.category_repo.get_by_id_accessible(data.category_id, user_id)
            if category is None:
                raise CategoryNotFoundException()
            expense.category_id = data.category_id

        if data.description is not None:
            expense.description = data.description
        if data.date_depense is not None:
            expense.date_depense = data.date_depense

        expense.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(expense)
        return expense

    # ---------- Suppression ----------

    async def delete_expense(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> None:
        expense = await self.get_expense(expense_id, user_id)

        # Recrédite le wallet du montant qui avait été débité (annule financièrement la dépense)
        wallet = await self.wallet_service.get_wallet(expense.wallet_id, user_id)
        montant_wallet = await self.exchange_service.convert(
            expense.montant, expense.devise, wallet.devise
        )
        await self.wallet_service.deposit(
            wallet_id=expense.wallet_id,
            user_id=user_id,
            montant=montant_wallet,
            reference=f"Remboursement suite à suppression: {expense.description or ''}",
        )

        await self.expense_repo.delete(expense)