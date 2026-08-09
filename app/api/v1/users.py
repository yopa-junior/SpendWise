# app/api/v1/users.py

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import os
from datetime import datetime

from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_verified_user),
):
    return UserResponse(
        id=str(current_user.id),
        nom=current_user.nom,
        email=current_user.email,
        devise_preferee=current_user.devise_preferee,
        langue_preferee=current_user.langue_preferee,
        fuseau_horaire=current_user.fuseau_horaire,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        photo_profil_url=current_user.photo_profil_url,
        telephone=current_user.telephone,
        date_creation=current_user.date_creation.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
    )


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    data: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    service = UserService(session)
    
    update_data = {}
    if data.nom is not None:
        update_data['nom'] = data.nom
    if data.devise_preferee is not None:
        update_data['devise_preferee'] = data.devise_preferee
    if data.langue_preferee is not None:
        update_data['langue_preferee'] = data.langue_preferee
    if data.telephone is not None:
        update_data['telephone'] = data.telephone
    if data.fuseau_horaire is not None:
        update_data['fuseau_horaire'] = data.fuseau_horaire
    if data.photo_profil_url is not None:
        update_data['photo_profil_url'] = data.photo_profil_url
    
    user = await service.update_profile(current_user.id, update_data)
    
    return UserResponse(
        id=str(user.id),
        nom=user.nom,
        email=user.email,
        devise_preferee=user.devise_preferee,
        langue_preferee=user.langue_preferee,
        fuseau_horaire=user.fuseau_horaire,
        is_active=user.is_active,
        is_verified=user.is_verified,
        photo_profil_url=user.photo_profil_url,
        telephone=user.telephone,
        date_creation=user.date_creation.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.post("/me/photo")
async def upload_profile_photo(
    photo: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Uploader une photo de profil"""
    try:
        # Valider le type de fichier
        if not photo.content_type or not photo.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le fichier doit être une image"
            )
        
        # Créer le dossier si inexistant
        upload_dir = "uploads/profiles"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Générer un nom de fichier unique
        extension = photo.filename.split('.')[-1] if photo.filename else 'jpg'
        filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"
        filepath = os.path.join(upload_dir, filename)
        
        # Sauvegarder le fichier
        with open(filepath, "wb") as f:
            content = await photo.read()
            f.write(content)
        
        # Construire l'URL (utiliser l'IP du serveur)
        # Pour le développement, utiliser l'IP locale
        # À CHANGER AVEC TON IP
        base_url = "http://10.180.179.130:8000"  # ← METS TON IP ICI
        photo_url = f"{base_url}/uploads/profiles/{filename}"
        
        # Mettre à jour l'utilisateur
        service = UserService(session)
        user = await service.update_profile(current_user.id, {"photo_profil_url": photo_url})
        
        return {
            "photo_profil_url": photo_url,
            "message": "Photo de profil mise à jour avec succès"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/me/photo")
async def delete_profile_photo(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Supprimer la photo de profil"""
    try:
        service = UserService(session)
        user = await service.update_profile(current_user.id, {"photo_profil_url": None})
        
        # Supprimer le fichier physique si existant
        if user.photo_profil_url:
            filename = user.photo_profil_url.split('/')[-1]
            filepath = f"uploads/profiles/{filename}"
            if os.path.exists(filepath):
                os.remove(filepath)
        
        return {"message": "Photo de profil supprimée"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )