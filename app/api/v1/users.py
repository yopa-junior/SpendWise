from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader
import uuid
from app.database.session import get_db
from app.dependencies.auth import get_current_verified_user
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse, FCMTokenUpdate
from app.services.user_service import UserService
from app.core.config import settings

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
    """Uploader une photo de profil vers Cloudinary"""

    try:
        # Vérifier le type de fichier
        if not photo.content_type or not photo.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le fichier doit être une image",
            )

        # Configurer Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )

        # Lire le fichier
        content = await photo.read()

        # Upload vers Cloudinary
        result = cloudinary.uploader.upload(
            content,
            folder="spendwise/profiles",
            public_id=str(current_user.id),
            overwrite=True,
            resource_type="image",
        )

        # URL permanente Cloudinary
        photo_url = result["secure_url"]

        # Enregistrer l'URL dans PostgreSQL
        service = UserService(session)

        user = await service.update_profile(
            current_user.id,
            {"photo_profil_url": photo_url},
        )

        return {
            "photo_profil_url": user.photo_profil_url,
            "message": "Photo de profil mise à jour avec succès",
        }

    except HTTPException:
        raise

    except Exception as e:
        print("========== CLOUDINARY ERROR ==========")
        print(str(e))
        print("======================================")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'upload de la photo",
        )

@router.delete("/me/photo")
async def delete_profile_photo(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Supprimer la photo de profil de Cloudinary"""

    try:
        # Récupérer l'ancienne URL AVANT de la supprimer
        old_photo_url = current_user.photo_profil_url

        if old_photo_url:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )

            # Le public_id correspond à spendwise/profiles/<user_id>
            public_id = f"spendwise/profiles/{current_user.id}"

            cloudinary.uploader.destroy(
                public_id,
                resource_type="image",
            )

        # Supprimer l'URL de la base de données
        service = UserService(session)

        await service.update_profile(
            current_user.id,
            {"photo_profil_url": None},
        )

        return {
            "message": "Photo de profil supprimée"
        }

    except Exception as e:
        print("========== CLOUDINARY DELETE ERROR ==========")
        print(str(e))
        print("=============================================")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de la photo",
        )

@router.post("/fcm-token", status_code=status.HTTP_204_NO_CONTENT)
async def register_fcm_token(
    data: FCMTokenUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """Enregistre ou met à jour le token FCM de l'utilisateur."""
    current_user.fcm_token = data.fcm_token
    await db.commit()
    # Pas de retour nécessaire, on renvoie juste 204 No Content