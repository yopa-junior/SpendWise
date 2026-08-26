from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(
    subject: str,
    recipients: list[str],
    template_name: str,
    template_body: dict,
) -> None:
    try:
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            template_body=template_body,
            subtype=MessageType.html,
        )

        fm = FastMail(conf)

        print("========== EMAIL DEBUG ==========")
        print(f"SMTP SERVER: {settings.MAIL_SERVER}")
        print(f"SMTP PORT: {settings.MAIL_PORT}")
        print(f"MAIL USERNAME: {settings.MAIL_USERNAME}")
        print(f"MAIL FROM: {settings.MAIL_FROM}")
        print(f"RECIPIENTS: {recipients}")
        print(f"TEMPLATE: {template_name}")
        print("=================================")

        await fm.send_message(
            message,
            template_name=template_name
        )

        print("========== EMAIL SENT ==========")
        print(f"Email envoyé à {recipients}")
        print("================================")

    except Exception as e:
        print("========== EMAIL ERROR ==========")
        print(f"Type: {type(e).__name__}")
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        print("=================================")
        raise