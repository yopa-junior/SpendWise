# app/exceptions/email_verification_exceptions.py

from fastapi import HTTPException, status


class InvalidOTPException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code de vérification incorrect",
        )


class ExpiredOTPException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce code a expiré, demande un nouveau code",
        )


class AlreadyUsedOTPException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce code a déjà été utilisé",
        )


class EmailAlreadyVerifiedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette adresse email est déjà vérifiée",
        )


class TooManyResendRequestsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de demandes de renvoi. Réessaie dans une heure merci.",
        )


class OTPBruteForceLockException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            detail="Trop de tentatives échouées. Réessaie dans 15 minutes.",
        )


class EmailNotVerifiedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merci de vérifier ton adresse email avant de te connecter",
        )


class IncorrectCurrentPasswordException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe actuel est incorrect",
        )       