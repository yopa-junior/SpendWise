# app/ai/chatbot.py

import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.ai.client import call_gemini_json, AIServiceError
from app.ai.schemas import ChatIntent, ChatResponseText
from app.ai.prompts import (
    CHATBOT_INTENT_PROMPT,
    CHATBOT_REPONSE_PROMPT,
    FALLBACK_NON_RECONNUE,
    FALLBACK_HORS_SUJET,
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
        print(f"DEBUG - raw_result intent: {raw_result}")  # temporaire
        return ChatIntent(**raw_result)
    except (AIServiceError, ValueError, TypeError) as e:
        return None

async def formulate_response(question: str, donnee: str) -> str:
    system_prompt = CHATBOT_REPONSE_PROMPT.format(question=question, donnee=donnee)
    try:
        raw_result = await call_gemini_json(system_prompt, question)
        result = ChatResponseText(**raw_result)
        return result.reponse
    except (AIServiceError, ValueError, TypeError) as e:
        return f"Voici l'information demandée : {donnee}"