import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
import uuid
import os

# Initialisation de Firebase Admin SDK
cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

async def send_push_notification(
    session: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    body: str,
    data: dict = None,
) -> bool:
    """
    Envoie une notification push à un utilisateur via FCM.
    Récupère le token FCM depuis la base de données.
    """
    # 1. Récupérer le token FCM de l'utilisateur
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.fcm_token:
        print(f"⚠️ Utilisateur {user_id} n'a pas de token FCM")
        return False

    # 2. Construire et envoyer le message
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        token=user.fcm_token,
    )
    try:
        response = messaging.send(message)
        print(f"✅ Notification envoyée à {user_id} : {response}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi à {user_id} : {e}")
        return False