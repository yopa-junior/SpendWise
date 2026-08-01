# app/exceptions/wallet_exceptions.py

from fastapi import HTTPException, status


class WalletNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet introuvable",
        )


class WalletInactiveException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce wallet est désactivé",
        )


class InsufficientBalanceException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solde insuffisant pour effectuer cette opération",
        )


class InvalidCurrencyException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Devise invalide ou inconnue",
        )
        
class SavingsGoalRequiresTargetException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Un objectif d'épargne doit avoir un montant cible",
        )