# app/schemas/user.py

from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import LanguePreferee


# ---------- Entrée : inscription ----------

class UserCreate(BaseModel):
    nom: str = Field(min_length=2, max_length=150)
    email: EmailStr
    mot_de_passe: str = Field(min_length=8, max_length=128)
    devise_preferee: str = Field(min_length=3, max_length=3)
    langue_preferee: LanguePreferee = LanguePreferee.FR

    @field_validator("mot_de_passe")
    @classmethod
    def valider_complexite(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v


# ---------- Entrée : connexion ----------

class UserLogin(BaseModel):
    email: EmailStr
    mot_de_passe: str


# ---------- Entrée : mise à jour du profil ----------

class UserUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=150)
    devise_preferee: str | None = Field(default=None, min_length=3, max_length=3)
    langue_preferee: LanguePreferee | None = None
    telephone: str | None = None
    fuseau_horaire: str | None = None
    photo_profil_url: Optional[str] = None


# ---------- Sortie : ce que l'API renvoie ----------

class UserResponse(BaseModel):
    id: uuid.UUID
    nom: str
    email: EmailStr
    devise_preferee: str | None
    langue_preferee: LanguePreferee
    fuseau_horaire: str
    is_active: bool
    is_verified: bool
    photo_profil_url: str | None
    telephone: str | None
    date_creation: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}
    

    
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(min_length=6, max_length=6, pattern=r"^[A-Z0-9]{6}$")
    nouveau_mot_de_passe: str = Field(min_length=8, max_length=128)

    @field_validator("nouveau_mot_de_passe")
    @classmethod
    def valider_complexite(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v


class ChangePasswordRequest(BaseModel):
    mot_de_passe_actuel: str
    nouveau_mot_de_passe: str = Field(min_length=8, max_length=128)

    @field_validator("nouveau_mot_de_passe")
    @classmethod
    def valider_complexite(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v