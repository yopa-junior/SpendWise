import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.notifications.email.mail import send_email


async def main():
    await send_email(
        subject="Test SpendWise",
        recipients=["ton_email_personnel@gmail.com"],  # remplace par ton email perso
        template_name="welcome.html",
        template_body={"nom": "Junior"},
    )
    print("Email envoyé avec succès")


if __name__ == "__main__":
    asyncio.run(main())