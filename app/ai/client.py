# app/ai/client.py

import asyncio
import json
import re

from google import genai

from app.core.config import settings


client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)

# Modèle utilisé par SpendWise
MODEL_NAME = "gemini-1.5-flash"

# Nombre maximum de tentatives
MAX_RETRIES = 3

# Timeout d'une tentative
TIMEOUT_SECONDS = 20.0


class AIServiceError(Exception):
    """Levée lorsqu'un appel Gemini échoue définitivement."""
    pass


def _extract_json(raw_text: str) -> str:
    """
    Extrait le premier objet JSON trouvé dans la réponse Gemini.
    """

    match = re.search(
        r"\{.*\}",
        raw_text,
        re.DOTALL,
    )

    if match is None:
        raise json.JSONDecodeError(
            "Aucun objet JSON trouvé dans la réponse",
            raw_text,
            0,
        )

    return match.group(0)


def _is_retryable_error(error: Exception) -> bool:
    """
    Détermine si l'erreur Gemini est probablement temporaire.

    On retente notamment pour :
    - 429 : trop de requêtes
    - 500 : erreur serveur
    - 502 : mauvaise passerelle
    - 503 : service temporairement indisponible
    - 504 : timeout côté serveur
    """

    message = str(error).lower()

    retryable_codes = [
        "429",
        "500",
        "502",
        "503",
        "504",
        "resource exhausted",
        "unavailable",
        "overloaded",
        "high demand",
        "temporarily",
    ]

    return any(
        code in message
        for code in retryable_codes
    )


async def _generate_content(
    system_prompt: str,
    user_message: str,
):
    """
    Effectue l'appel Gemini avec retry automatique.
    """

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            print(
                f"========== GEMINI TENTATIVE {attempt}/{MAX_RETRIES} =========="
            )

            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=MODEL_NAME,
                    contents=user_message,
                    config={
                        "system_instruction": system_prompt,
                    },
                ),
                timeout=TIMEOUT_SECONDS,
            )

            print(
                "========== GEMINI APPEL RÉUSSI =========="
            )

            return response

        except asyncio.TimeoutError as e:

            last_error = e

            print(
                f"Gemini timeout lors de la tentative {attempt}"
            )

            if attempt < MAX_RETRIES:
                delay = 2 ** (attempt - 1)

                print(
                    f"Nouvelle tentative dans {delay} seconde(s)..."
                )

                await asyncio.sleep(delay)

        except Exception as e:

            last_error = e

            print(
                f"========== ERREUR GEMINI TENTATIVE {attempt} =========="
            )
            print(type(e).__name__)
            print(str(e))
            print("=========================================================")

            # Si l'erreur n'est probablement pas temporaire,
            # inutile de faire trois appels.
            if not _is_retryable_error(e):
                break

            if attempt < MAX_RETRIES:

                delay = 2 ** (attempt - 1)

                print(
                    f"Erreur temporaire. Nouvelle tentative dans "
                    f"{delay} seconde(s)..."
                )

                await asyncio.sleep(delay)

    raise AIServiceError(
        f"Gemini indisponible après {MAX_RETRIES} tentative(s): "
        f"{last_error}"
    )


async def call_gemini_json(
    system_prompt: str,
    user_message: str,
) -> dict:
    """
    Appelle Gemini lorsqu'une réponse JSON est attendue.
    """

    try:

        response = await _generate_content(
            system_prompt,
            user_message,
        )

        raw_text = response.text.strip()

        print(
            "========== GEMINI JSON RAW RESPONSE =========="
        )
        print(raw_text)
        print(
            "==============================================="
        )

        json_text = _extract_json(raw_text)

        return json.loads(json_text)

    except AIServiceError:
        raise

    except json.JSONDecodeError as e:

        raise AIServiceError(
            f"Réponse Gemini non conforme au JSON attendu: {e}"
        ) from e

    except Exception as e:

        raise AIServiceError(
            f"Erreur lors du traitement de la réponse Gemini: {e}"
        ) from e


async def call_gemini_text(
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Appelle Gemini lorsqu'une réponse textuelle normale est attendue.
    """

    try:

        response = await _generate_content(
            system_prompt,
            user_message,
        )

        raw_text = response.text.strip()

        print(
            "========== GEMINI TEXT RAW RESPONSE =========="
        )
        print(raw_text)
        print(
            "==============================================="
        )

        if not raw_text:

            raise AIServiceError(
                "Gemini a retourné une réponse vide."
            )

        return raw_text

    except AIServiceError:
        raise

    except Exception as e:

        raise AIServiceError(
            f"Erreur lors du traitement de la réponse Gemini: {e}"
        ) from e