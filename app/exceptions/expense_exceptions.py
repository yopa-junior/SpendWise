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
        
class CategoryHasExpensesException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Impossible de supprimer cette catégorie : des dépenses y sont encore associées",
        )
        
        
class NoReferenceCurrencyException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucune devise de référence définie. Précise une devise ou configure ta devise préférée dans ton profil.",
        )