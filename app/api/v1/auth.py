from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token, RefreshTokenRequest, GoogleLoginRequest  # ✅ Ajouté
from app.services.auth_service import AuthService
from app.schemas.user import ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
from app.schemas.email_verification import (
    VerifyEmailRequest,
    ResendOTPRequest,
    VerifyEmailResponse,
)
from app.services.email_verification_service import EmailVerificationService

router = APIRouter(prefix="/auth", tags=["Authentification"])

# Ton Client ID Google
CLIENT_ID = "36431335038-ql7ego7lhjf2a8ukh1h2eeae2ijkma4g.apps.googleusercontent.com"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(data)
    return user


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    
    # Vérification du compte Google avant authentification
    user = await service.user_repo.get_by_email(data.email)
    if user and user.mot_de_passe_hash is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte a été créé via Google. Veuillez utiliser 'Mot de passe oublié' pour définir un mot de passe."
        )
    
    user = await service.authenticate(data.email, data.mot_de_passe)
    return await service.create_tokens(user)


@router.post("/google-login", response_model=Token) 
async def google_login(data: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    
    try:
        # Vérification officielle du token Google
        info = id_token.verify_oauth2_token(
            data.id_token,
            requests.Request(),
            CLIENT_ID
        )
        email = info.get("email")
        nom = info.get("name", "Utilisateur Google")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email non trouvé dans le token Google")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Token Google invalide ou expiré: {str(e)}")

    # Cherche ou crée l'utilisateur
    user = await service.user_repo.get_by_email(email)
    if user is None:
        user = await service.register_google_user(email=email, nom=nom)

    return await service.create_tokens(user)


@router.post("/refresh", response_model=Token)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh_access_token(data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.logout(data.refresh_token)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.logout_all_devices(current_user.id)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(data: ForgotPasswordRequest, session: AsyncSession = Depends(get_db)):
    service = AuthService(session)
    await service.forgot_password(data.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(data: ResetPasswordRequest, session: AsyncSession = Depends(get_db)):
    service = AuthService(session)
    await service.reset_password(data.email, data.otp_code, data.nouveau_mot_de_passe)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AuthService(session)
    await service.change_password(current_user, data.mot_de_passe_actuel, data.nouveau_mot_de_passe)


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(data: VerifyEmailRequest, session: AsyncSession = Depends(get_db)):
    service = EmailVerificationService(session)
    await service.verify_code(data.email, data.otp_code)
    return VerifyEmailResponse(message="Email vérifié avec succès", is_verified=True)


@router.post("/resend-code", status_code=status.HTTP_204_NO_CONTENT)
async def resend_code(data: ResendOTPRequest, session: AsyncSession = Depends(get_db)):
    service = EmailVerificationService(session)
    await service.resend_code(data.email)