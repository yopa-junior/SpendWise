# app/repositories/email_verification_repository.py

import uuid
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification import EmailVerification, OTPPurpose
from app.repositories.base_repository import BaseRepository


class EmailVerificationRepository(BaseRepository[EmailVerification]):
    def __init__(self, session: AsyncSession):
        super().__init__(EmailVerification, session)

    async def create(self, obj: EmailVerification) -> EmailVerification:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def find_valid_code(
        self, user_id: uuid.UUID, otp_code: str, purpose: OTPPurpose
    ) -> EmailVerification | None:
        """Trouve un code non expiré, non utilisé, correspondant exactement."""
        result = await self.session.execute(
            select(EmailVerification).where(
                EmailVerification.user_id == user_id,
                EmailVerification.otp_code == otp_code,
                EmailVerification.purpose == purpose,
                EmailVerification.is_used == False,  # noqa: E712
                EmailVerification.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def latest_code(
        self, user_id: uuid.UUID, purpose: OTPPurpose
    ) -> EmailVerification | None:
        """Récupère le dernier code généré pour cet utilisateur/usage, peu importe son état."""
        result = await self.session.execute(
            select(EmailVerification)
            .where(
                EmailVerification.user_id == user_id,
                EmailVerification.purpose == purpose,
            )
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_recent_requests(
        self, user_id: uuid.UUID, purpose: OTPPurpose, since: datetime
    ) -> int:
        """Compte les codes générés depuis un instant donné (pour limiter les renvois)."""
        result = await self.session.execute(
            select(EmailVerification).where(
                EmailVerification.user_id == user_id,
                EmailVerification.purpose == purpose,
                EmailVerification.created_at >= since,
            )
        )
        return len(result.scalars().all())

    async def mark_as_used(self, verification: EmailVerification) -> None:
        verification.is_used = True
        await self.session.commit()

    async def increment_attempts(self, verification: EmailVerification) -> None:
        verification.attempts += 1
        await self.session.commit()

    async def delete_expired(self) -> int:
        """Supprime tous les codes expirés depuis plus de 24h (nettoyage périodique)."""
        cutoff = datetime.now(timezone.utc)
        result = await self.session.execute(
            delete(EmailVerification).where(EmailVerification.expires_at < cutoff)
        )
        await self.session.commit()
        return result.rowcount