# app/ai/categorizer.py

import hashlib
from app.ai.client import call_gemini_json, AIServiceError
from app.ai.prompts import CATEGORIZATION_SYSTEM_PROMPT
from app.ai.schemas import CategorizationResult

# Cache en mémoire : clé = hash de la description normalisée, valeur = résultat
_categorization_cache: dict[str, CategorizationResult] = {}


def _normalize_description(description: str) -> str:
    return description.strip().lower()


def _cache_key(description: str) -> str:
    normalized = _normalize_description(description)
    return hashlib.sha256(normalized.encode()).hexdigest()


async def suggest_category(description: str, categories_disponibles: list[str]) -> CategorizationResult | None:
    """
    Suggère une catégorie pour une description de dépense.
    Retourne None si l'IA est indisponible (fallback : l'utilisateur choisit manuellement).
    """
    cache_key = _cache_key(description)
    if cache_key in _categorization_cache:
        return _categorization_cache[cache_key]

    system_prompt = CATEGORIZATION_SYSTEM_PROMPT.format(
        categories_disponibles=", ".join(categories_disponibles)
    )

    try:
        raw_result = await call_gemini_json(system_prompt, description)
        result = CategorizationResult(**raw_result)
    except (AIServiceError, ValueError, TypeError) as e:
        
        return None

    # Vérification défensive : la catégorie suggérée doit être exactement dans la liste connue
    if result.categorie_nom not in categories_disponibles:
        return None

    _categorization_cache[cache_key] = result
    return result