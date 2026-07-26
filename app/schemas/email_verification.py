# app/schemas/email_verification.py

from pydantic import BaseModel, EmailStr, Field


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(min_length=6, max_length=6, pattern=r"^[A-Z0-9]{6}$")


class ResendOTPRequest(BaseModel):
    email: EmailStr


class VerifyEmailResponse(BaseModel):
    message: str
    is_verified: bool


class CheckVerificationResponse(BaseModel):
    email: str
    is_verified: bool