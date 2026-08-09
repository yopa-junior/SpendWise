# app/exceptions/ai_exceptions.py

from fastapi import HTTPException, status


class AIQuotaExceededException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Limite quotidienne d'appels IA atteinte. Réessaie demain.",
        )


class AIUnavailableException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service de catégorisation automatique est temporairement indisponible.",
        )