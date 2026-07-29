# app/ai/client.py

import json
import asyncio
from google import genai

from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL_NAME = "gemini-flash-latest"
TIMEOUT_SECONDS = 5.0


class AIServiceError(Exception):
    """Levée quand l'appel IA échoue ou renvoie un format invalide."""
    pass


async def call_gemini_json(system_prompt: str, user_message: str) -> dict:
    """
    Appelle Gemini et force une réponse JSON stricte.
    Lève AIServiceError en cas d'échec réseau, timeout, ou JSON invalide.
    """
    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=user_message,
                config={"system_instruction": system_prompt},
            ),
            timeout=TIMEOUT_SECONDS,
        )
        raw_text = response.text.strip()

        # Nettoyage défensif : Gemini peut parfois entourer le JSON de balises markdown
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").removeprefix("json").strip()

        return json.loads(raw_text)

    except asyncio.TimeoutError as e:
        raise AIServiceError("Délai d'attente dépassé pour la réponse IA") from e
    except json.JSONDecodeError as e:
        raise AIServiceError(f"Réponse IA non conforme au format JSON attendu: {e}") from e
    except Exception as e:
        raise AIServiceError(f"Erreur API Gemini: {e}") from e