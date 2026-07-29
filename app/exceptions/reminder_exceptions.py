# app/exceptions/reminder_exceptions.py

from fastapi import HTTPException, status


class ReminderNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rappel introuvable",
        )


class InvalidReminderDayException(HTTPException):
    def __init__(self, frequence: str):
        if frequence == "mensuel":
            detail = "Le jour d'échéance doit être compris entre 1 et 31 pour une fréquence mensuelle"
        else:
            detail = "Le jour d'échéance doit être compris entre 0 (lundi) et 6 (dimanche) pour une fréquence hebdomadaire"
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)