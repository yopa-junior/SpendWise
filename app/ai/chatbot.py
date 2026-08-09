import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.ai.client import call_gemini_json, AIServiceError
from app.ai.schemas import ChatIntent, ChatResponseText
from app.ai.prompts import (
    CHATBOT_INTENT_PROMPT,
    CHATBOT_REPONSE_PROMPT,
    CHATBOT_OPEN_PROMPT,  
    FALLBACK_NON_RECONNUE,
    FALLBACK_ERREUR_IA,
)


def _resolve_period(periode_label: str | None) -> tuple[date, date]:
    """Convertit un label de période en dates concrètes de début/fin."""
    today = date.today()

    if periode_label == "mois_dernier":
        premier_jour_mois_actuel = today.replace(day=1)
        dernier_jour_mois_precedent = premier_jour_mois_actuel - timedelta(days=1)
        premier_jour_mois_precedent = dernier_jour_mois_precedent.replace(day=1)
        return premier_jour_mois_precedent, dernier_jour_mois_precedent

    if periode_label == "cette_semaine":
        debut_semaine = today - timedelta(days=today.weekday())
        return debut_semaine, today

    # Par défaut : ce mois-ci
    return today.replace(day=1), today


async def detect_intent(question: str, categories_disponibles: list[str]) -> ChatIntent | None:
    system_prompt = CHATBOT_INTENT_PROMPT.format(
        categories_disponibles=", ".join(categories_disponibles)
    )
    try:
        raw_result = await call_gemini_json(system_prompt, question)
        return ChatIntent(**raw_result)
    except (AIServiceError, ValueError, TypeError) as e:
        return None


async def formulate_response(question: str, donnee: str, historique: list = None) -> str:
    """
    Formule une réponse en français à partir des données calculées.
    Si un historique est fourni, il est injecté dans le prompt pour assurer la continuité de la conversation.
    """
    system_prompt = CHATBOT_REPONSE_PROMPT.format(question=question, donnee=donnee)
    
    # Ajout de la mémoire de conversation
    if historique and len(historique) > 0:
        contexte = "\n\nVoici l'historique de la conversation précédente avec l'utilisateur, souviens-t'en pour répondre de manière cohérente :\n"
        for msg in historique[-5:]:
            contexte += f"- {msg['role']} a dit : {msg['content']}\n"
        system_prompt += contexte

    try:
        raw_result = await call_gemini_json(system_prompt, question)
        result = ChatResponseText(**raw_result)
        return result.reponse
    except (AIServiceError, ValueError, TypeError) as e:
        return f"Voici l'information demandée : {donnee}"


async def answer_open_question(question: str) -> str:
    """Répond librement à une question hors du périmètre financier, sans données utilisateur réelles."""
    try:
        raw_result = await call_gemini_json(CHATBOT_OPEN_PROMPT, question)
        result = ChatResponseText(**raw_result)
        return result.reponse
    except (AIServiceError, ValueError, TypeError):
        return FALLBACK_ERREUR_IA