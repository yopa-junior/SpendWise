from datetime import date, timedelta
from typing import Optional, List, Dict

from app.ai.client import (
    call_gemini_json,
    call_gemini_text,
    AIServiceError,
)
from app.ai.schemas import ChatIntent, ChatResponseText
from app.ai.prompts import (
    CHATBOT_INTENT_PROMPT,
    CHATBOT_REPONSE_PROMPT,
    CHATBOT_OPEN_PROMPT,
    FALLBACK_ERREUR_IA,
)


def _resolve_period(periode_label: str | None) -> tuple[date, date]:
    """
    Convertit une période détectée par l'IA en dates concrètes.
    """

    today = date.today()

    if periode_label == "mois_dernier":
        premier_jour_mois_actuel = today.replace(day=1)

        dernier_jour_mois_precedent = (
            premier_jour_mois_actuel - timedelta(days=1)
        )

        premier_jour_mois_precedent = (
            dernier_jour_mois_precedent.replace(day=1)
        )

        return (
            premier_jour_mois_precedent,
            dernier_jour_mois_precedent,
        )

    if periode_label == "cette_semaine":
        debut_semaine = today - timedelta(days=today.weekday())

        return (
            debut_semaine,
            today,
        )

    # Par défaut : ce mois-ci
    return (
        today.replace(day=1),
        today,
    )


def _build_history_context(
    historique: Optional[List[Dict[str, str]]],
    limit: int = 10,
) -> str:
    """
    Construit le contexte textuel à partir de l'historique.

    L'historique vient du frontend Flutter.
    """

    if not historique:
        return ""

    messages = historique[-limit:]

    contexte = (
        "\n\nHISTORIQUE RÉCENT DE LA CONVERSATION :\n"
        "Utilise cet historique pour comprendre les références "
        "comme « et le mois dernier », « et cette catégorie », "
        "« pourquoi ? », « explique-moi davantage », etc.\n\n"
    )

    for msg in messages:
        role = msg.get("role", "utilisateur")
        content = msg.get("content", "").strip()

        if not content:
            continue

        contexte += f"{role}: {content}\n"

    return contexte


async def detect_intent(
    question: str,
    categories_disponibles: list[str],
    historique: Optional[List[Dict[str, str]]] = None,
) -> ChatIntent | None:
    """
    Détecte l'intention de la question.

    IMPORTANT :
    La question actuelle est analysée avec l'historique afin que
    Gemini puisse comprendre les questions contextuelles.

    Exemple :

    Utilisateur :
        Combien ai-je dépensé ce mois-ci ?

    Puis :
        Et le mois dernier ?

    Gemini doit comprendre que « le mois dernier » concerne
    toujours les dépenses de l'utilisateur.
    """

    system_prompt = CHATBOT_INTENT_PROMPT.format(
        categories_disponibles=", ".join(categories_disponibles)
    )

    # Ajout de l'historique AVANT l'analyse de la question.
    system_prompt += _build_history_context(
        historique,
        limit=10,
    )

    system_prompt += (
        "\n\nQUESTION ACTUELLE DE L'UTILISATEUR :\n"
        f"{question}\n\n"
        "Analyse la question actuelle en tenant compte de l'historique. "
        "Si la question est une suite logique de la conversation précédente, "
        "utilise le contexte précédent pour déterminer correctement "
        "l'intention, la catégorie et la période."
    )

    try:
        raw_result = await call_gemini_json(
            system_prompt,
            question,
        )

        return ChatIntent(**raw_result)

    except (
        AIServiceError,
        ValueError,
        TypeError,
    ) as e:

        print("========== ERREUR DETECTION INTENTION ==========")
        print(type(e).__name__)
        print(str(e))
        print("=================================================")

        return None


async def formulate_response(
    question: str,
    donnee: str,
    historique: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Transforme une donnée financière calculée par le backend
    en réponse naturelle.

    IMPORTANT :
    Le backend fournit déjà le chiffre exact.
    Gemini ne doit jamais recalculer ou modifier cette donnée.
    """

    system_prompt = CHATBOT_REPONSE_PROMPT.format(
        question=question,
        donnee=donnee,
    )

    # Ajout de l'historique.
    system_prompt += _build_history_context(
        historique,
        limit=10,
    )

    system_prompt += (
        "\n\nRéponds directement à la question actuelle. "
        "Utilise l'historique uniquement pour comprendre le contexte. "
        "Ne crée aucune donnée financière qui n'est pas fournie."
    )

    try:
        raw_result = await call_gemini_json(
            system_prompt,
            question,
        )

        result = ChatResponseText(**raw_result)

        return result.reponse

    except (
        AIServiceError,
        ValueError,
        TypeError,
    ) as e:

        print("========== ERREUR FORMULATION RÉPONSE ==========")
        print(type(e).__name__)
        print(str(e))
        print("=================================================")

        # La donnée calculée par le backend reste toujours fiable.
        return f"Voici l'information demandée : {donnee}"


async def answer_open_question(
    question: str,
    historique: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Répond aux questions générales et aux questions concernant SpendWise.

    Cette fonction utilise une réponse textuelle normale et non du JSON.

    L'historique permet également de comprendre les questions
    générales qui font référence aux messages précédents.
    """

    system_prompt = CHATBOT_OPEN_PROMPT

    system_prompt += _build_history_context(
        historique,
        limit=10,
    )

    system_prompt += (
        "\n\nQUESTION ACTUELLE :\n"
        f"{question}\n\n"
        "Réponds à cette question en tenant compte du contexte "
        "de la conversation lorsque cela est nécessaire."
    )

    try:
        response = await call_gemini_text(
            system_prompt,
            question,
        )

        return response.strip()

    except AIServiceError as e:

        print("========== ERREUR QUESTION GENERALE ==========")
        print(type(e).__name__)
        print(str(e))
        print("===============================================")

        return FALLBACK_ERREUR_IA