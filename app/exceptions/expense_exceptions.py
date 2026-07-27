# app/exceptions/expense_exceptions.py

from fastapi import HTTPException, status


class ExchangeRateNotFoundException(HTTPException):
    def __init__(self, devise_source: str, devise_cible: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Aucun taux de change disponible entre {devise_source} et {devise_cible}",
        )


class ExpenseNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dépense introuvable",
        )