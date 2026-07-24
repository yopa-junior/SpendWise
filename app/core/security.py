# app/core/security.py

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# Contexte de hashage des mots de passe
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ---------- Mots de passe ----------

def hash_password(password: str) -> str:
    """Hash un mot de passe en clair avec Argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------- Access Token (JWT) ----------

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Génère un JWT signé contenant l'id utilisateur (subject).
    Durée de vie courte, définie dans la config.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Décode et vérifie un JWT.
    Retourne le payload si valide, None si invalide/expiré.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ---------- Refresh Token ----------

def generate_refresh_token() -> str:
    """
    Génère un refresh token opaque et aléatoire (pas un JWT).
    On ne le décode jamais : on compare son hash stocké en base.
    """
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """
    Hash le refresh token avant stockage en base (SHA-256 suffit ici,
    car le token est déjà aléatoire à haute entropie, contrairement
    à un mot de passe utilisateur qui a besoin d'Argon2).
    """
    return hashlib.sha256(token.encode()).hexdigest()