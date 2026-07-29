# app/schemas/notification.py

import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    id: uuid.UUID
    type: NotificationType
    titre: str
    message: str
    reference_id: uuid.UUID | None
    lu: bool
    date: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int