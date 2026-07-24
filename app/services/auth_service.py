# app/services/auth_service.py

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user import UserCreate
from app.schemas.token import Token

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)

    # ---------- Inscription ----------

    async def register(self, data: UserCreate) -> User:
        if await self.user_repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un compte existe déjà avec cet email",
            )

        user = User(
            nom=data.nom,
            email=data.email,
            mot_de_passe_hash=hash_password(data.mot_de_passe),
            devise_preferee=data.devise_preferee,
            langue_preferee=data.langue_preferee,
        )
        return await self.user_repo.create(user)

    # ---------- Connexion ----------

    async def authenticate(self, email: str, mot_de_passe: str) -> User:
        user = await self.user_repo.get_by_email(email)

        # Message générique volontaire : ne jamais révéler si l'email existe
        generic_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

        if user is None:
            raise generic_error

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Compte temporairement verrouillé suite à trop de tentatives. Réessayez plus tard.",
            )

        if not verify_password(mot_de_passe, user.mot_de_passe_hash):
            await self.user_repo.increment_failed_attempts(user)

            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)
                await self.user_repo.lock_account(user, locked_until)
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Trop de tentatives échouées. Compte verrouillé 15 minutes.",
                )

            raise generic_error

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ce compte a été désactivé",
            )

        await self.user_repo.reset_failed_attempts(user)
        await self.user_repo.update_last_login(user)
        return user

    # ---------- Génération des tokens ----------

    async def create_tokens(self, user: User) -> Token:
        access_token = create_access_token(subject=str(user.id))

        raw_refresh_token = generate_refresh_token()
        token_entity = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            revoked=False,
            created_at=datetime.now(timezone.utc),
        )
        await self.refresh_repo.create(token_entity)

        return Token(access_token=access_token, refresh_token=raw_refresh_token)

    # ---------- Rafraîchissement de l'access token ----------

    async def refresh_access_token(self, raw_refresh_token: str) -> Token:
        token_hash = hash_refresh_token(raw_refresh_token)
        token_entity = await self.refresh_repo.get_by_token_hash(token_hash)

        invalid_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré",
        )

        if token_entity is None:
            raise invalid_error

        if not await self.refresh_repo.is_valid(token_entity):
            raise invalid_error

        user = await self.user_repo.get_by_id(token_entity.user_id)
        if user is None or not user.is_active:
            raise invalid_error

        # Rotation : on révoque l'ancien refresh token et on en émet un nouveau
        await self.refresh_repo.revoke(token_entity)
        return await self.create_tokens(user)

    # ---------- Déconnexion ----------

    async def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_refresh_token(raw_refresh_token)
        token_entity = await self.refresh_repo.get_by_token_hash(token_hash)
        if token_entity is not None:
            await self.refresh_repo.revoke(token_entity)

    async def logout_all_devices(self, user_id: uuid.UUID) -> None:
        await self.refresh_repo.revoke_all_for_user(user_id)