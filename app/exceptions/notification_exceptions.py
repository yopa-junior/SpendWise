# app/exceptions/notification_exceptions.py

from fastapi import HTTPException, status


class NotificationNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification introuvable",
        )