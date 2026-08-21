import secrets
import uuid
from datetime import datetime, timedelta, timezone

from markupsafe import Markup
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification import EmailVerification, OTPPurpose
from app.models.user import User
from app.repositories.email_verification_repository import EmailVerificationRepository
from app.repositories.user_repository import UserRepository
from app.notifications.email.mail import send_email
from app.exceptions.email_verification_exceptions import (
    InvalidOTPException,
    ExpiredOTPException,
    AlreadyUsedOTPException,
    EmailAlreadyVerifiedException,
    TooManyResendRequestsException,
    OTPBruteForceLockException,
)

OTP_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans I, O, 0, 1 (ambiguïté visuelle)
OTP_LENGTH = 6
OTP_EXPIRE_MINUTES = 10
MAX_VERIFY_ATTEMPTS = 5
VERIFY_LOCK_MINUTES = 15
MAX_RESEND_PER_HOUR = 5

COLORS = ["#2563eb", "#dc2626", "#059669", "#f59e0b", "#7c3aed", "#db2777"]


class EmailVerificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.verification_repo = EmailVerificationRepository(session)
        self.user_repo = UserRepository(session)

    # ---------- Génération du code ----------

    def generate_otp(self) -> str:
        """
        Génère un code alphanumérique aléatoire cryptographiquement sûr.
        Utilise secrets.choice (jamais random) pour garantir l'imprévisibilité.
        """
        return "".join(secrets.choice(OTP_ALPHABET) for _ in range(OTP_LENGTH))

    def _build_colored_otp_html(self, otp_code: str) -> Markup:
        """
        Construit une représentation HTML du code OTP,
        où chaque caractère a une couleur différente (cycle sur COLORS).
        Markup empêche Jinja2 d'échapper les balises HTML.
        """
        spans = []
        for i, char in enumerate(otp_code):
            color = COLORS[i % len(COLORS)]
            spans.append(f'<span style="color:{color};">{char}</span>')
        return Markup("".join(spans))

    # ---------- Création et envoi ----------

    async def create_verification(
        self, user: User, purpose: OTPPurpose = OTPPurpose.EMAIL_VERIFICATION
    ) -> EmailVerification:
        """Génère un nouveau code, l'enregistre en base et l'envoie par email."""
        otp_code = self.generate_otp()

        verification = EmailVerification(
            user_id=user.id,
            email=user.email,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
            is_used=False,
            attempts=0,
            created_at=datetime.now(timezone.utc),
        )
        verification = await self.verification_repo.create(verification)

        await self._send_otp_email(user, otp_code, purpose)  # ✅ Passage du purpose
        return verification

    async def _send_otp_email(self, user: User, otp_code: str, purpose: OTPPurpose) -> None:
        if purpose == OTPPurpose.EMAIL_VERIFICATION:
            otp_html = self._build_colored_otp_html(otp_code)
            await send_email(
                subject="🎉 Ton code de vérification SpendWise",
                recipients=[user.email],
                template_name="otp_email.html",
                template_body={
                    "nom": user.nom,
                    "otp_html": otp_html,
                    "expiration_minutes": OTP_EXPIRE_MINUTES,
                },
            )
        elif purpose == OTPPurpose.PASSWORD_RESET:
            reset_link = f"https://spendwise.app/reset-password?code={otp_code}&email={user.email}"
            await send_email(
                subject="🔐 Réinitialisation de ton mot de passe SpendWise",
                recipients=[user.email],
                template_name="reset_password_email.html",
                template_body={
                    "nom": user.nom,
                    "reset_link": reset_link,
                    "expiration_minutes": OTP_EXPIRE_MINUTES,
                },
            )

    # ---------- Vérification du code ----------

    async def verify_code(
        self, email: str, otp_code: str, purpose: OTPPurpose = OTPPurpose.EMAIL_VERIFICATION
    ) -> User:
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise InvalidOTPException()  # message générique volontaire, ne révèle pas si l'email existe

        if user.is_verified and purpose == OTPPurpose.EMAIL_VERIFICATION:
            raise EmailAlreadyVerifiedException()

        latest = await self.verification_repo.latest_code(user.id, purpose)

        # Anti brute-force : trop de tentatives sur le dernier code généré
        if latest is not None and latest.attempts >= MAX_VERIFY_ATTEMPTS:
            lock_expires = latest.created_at + timedelta(minutes=VERIFY_LOCK_MINUTES)
            if datetime.now(timezone.utc) < lock_expires:
                raise OTPBruteForceLockException()

        verification = await self.verification_repo.find_valid_code(user.id, otp_code, purpose)

        if verification is None:
            # Le code est soit inexistant, soit expiré, soit déjà utilisé, soit incorrect
            if latest is not None:
                await self.verification_repo.increment_attempts(latest)

                if latest.is_used:
                    raise AlreadyUsedOTPException()
                if latest.expires_at < datetime.now(timezone.utc):
                    raise ExpiredOTPException()

            raise InvalidOTPException()

        await self.verification_repo.mark_as_used(verification)

        if purpose == OTPPurpose.EMAIL_VERIFICATION:
            await self.user_repo.update(user, is_verified=True)

        return user

    # ---------- Renvoi du code ----------

    async def resend_code(
        self, email: str, purpose: OTPPurpose = OTPPurpose.EMAIL_VERIFICATION
    ) -> EmailVerification:
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise InvalidOTPException()  # même logique : ne pas révéler l'existence du compte

        if user.is_verified and purpose == OTPPurpose.EMAIL_VERIFICATION:
            raise EmailAlreadyVerifiedException()

        since = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_count = await self.verification_repo.count_recent_requests(user.id, purpose, since)

        if recent_count >= MAX_RESEND_PER_HOUR:
            raise TooManyResendRequestsException()

        return await self.create_verification(user, purpose)

    # ---------- Nettoyage périodique ----------

    async def cleanup_expired_codes(self) -> int:
        """A appeler depuis une tâche planifiée (Celery/APScheduler)."""
        return await self.verification_repo.delete_expired()