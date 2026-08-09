# app/repositories/wallet_repository.py

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet
from app.repositories.base_repository import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    def __init__(self, session: AsyncSession):
        super().__init__(Wallet, session)

    async def get_by_id_and_user(self, wallet_id: uuid.UUID, user_id: uuid.UUID) -> Wallet | None:
        """Récupère un wallet en s'assurant qu'il appartient bien à l'utilisateur demandeur."""
        result = await self.session.execute(
            select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID, active_only: bool = True) -> list[Wallet]:
        query = select(Wallet).where(Wallet.user_id == user_id)
        if active_only:
            query = query.where(Wallet.is_active == True)  # noqa: E712
        result = await self.session.execute(query.order_by(Wallet.created_at))
        return list(result.scalars().all())

    async def update_solde(self, wallet: Wallet, nouveau_solde) -> Wallet:
        wallet.solde = nouveau_solde
        await self.session.commit()
        await self.session.refresh(wallet)
        return wallet