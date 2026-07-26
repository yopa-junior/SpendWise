# app/models/email_verification.py

import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OTPPurpose(str, enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    EMAIL_CHANGE = "email_change"


class EmailVerification(Base):
    __tablename__ = "email_verifications"
    __table_args__ = (
        Index("ix_email_verifications_user_purpose", "user_id", "purpose"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    otp_code: Mapped[str] = mapped_column(String(6), nullable=False, index=True)
    purpose: Mapped[OTPPurpose] = mapped_column(
        SQLEnum(OTPPurpose), default=OTPPurpose.EMAIL_VERIFICATION, nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Anti brute-force spécifique à ce code
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="email_verifications")

    def __repr__(self) -> str:
        return f"<EmailVerification user_id={self.user_id} purpose={self.purpose} used={self.is_used}>"