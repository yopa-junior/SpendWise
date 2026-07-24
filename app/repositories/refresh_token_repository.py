# app/repositories/refresh_token_repository.py

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def is_valid(self, token: RefreshToken) -> bool:
        if token.revoked:
            return False
        if token.expires_at < datetime.now(timezone.utc):
            return False
        return True

    async def revoke(self, token: RefreshToken) -> None:
        token.revoked = True
        await self.session.commit()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Révoque toutes les sessions d'un utilisateur (ex: changement de mot de passe, déconnexion globale)."""
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        tokens = result.scalars().all()
        for t in tokens:
            t.revoked = True
        await self.session.commit()