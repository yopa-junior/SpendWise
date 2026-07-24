# app/schemas/token.py

from pydantic import BaseModel


class Token(BaseModel):
    """Réponse renvoyée après une connexion réussie."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Contenu décodé d'un access token JWT."""
    sub: str  # id de l'utilisateur
    exp: int
    type: str


class RefreshTokenRequest(BaseModel):
    """Corps de la requête pour demander un nouvel access token."""
    refresh_token: str