# app/services/user_service.py

from typing import Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def update_profile(self, user_id: uuid.UUID, data: dict) -> User:
        """
        Mettre à jour le profil d'un utilisateur.
        Les champs autorisés sont : nom, devise_preferee, langue_preferee,
        telephone, fuseau_horaire, photo_profil_url
        """
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("Utilisateur non trouvé")

        # Mettre à jour les champs
        if "nom" in data and data["nom"] is not None:
            user.nom = data["nom"]
        if "devise_preferee" in data and data["devise_preferee"] is not None:
            user.devise_preferee = data["devise_preferee"]
        if "langue_preferee" in data and data["langue_preferee"] is not None:
            user.langue_preferee = data["langue_preferee"]
        if "telephone" in data and data["telephone"] is not None:
            user.telephone = data["telephone"]
        if "fuseau_horaire" in data and data["fuseau_horaire"] is not None:
            user.fuseau_horaire = data["fuseau_horaire"]
        if "photo_profil_url" in data:
            user.photo_profil_url = data["photo_profil_url"]

        user.updated_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user