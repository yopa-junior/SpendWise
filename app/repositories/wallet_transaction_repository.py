# app/repositories/wallet_transaction_repository.py

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet_transaction import WalletTransaction
from app.repositories.base_repository import BaseRepository


class WalletTransactionRepository(BaseRepository[WalletTransaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(WalletTransaction, session)

    async def create(self, obj: WalletTransaction) -> WalletTransaction:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def list_by_wallet(self, wallet_id: uuid.UUID) -> list[WalletTransaction]:
        result = await self.session.execute(
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet_id)
            .order_by(WalletTransaction.created_at.desc())
        )
        return list(result.scalars().all())