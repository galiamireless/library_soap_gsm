from __future__ import annotations

import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode


def send_verification_email(settings, recipient: str, token: str) -> None:
    url = f"{settings.verification_url}?{urlencode({'token': token, 'format': 'json'})}"
    message = EmailMessage()
    message["Subject"] = "Verifica tu cuenta de Library"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(f"Confirma tu cuenta visitando este enlace: {url}")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        smtp.send_message(message)


def print_verification_email(settings, recipient: str, token: str) -> None:
    url = f"{settings.verification_url}?{urlencode({'token': token, 'format': 'json'})}"
    print(f"[LOGIN_EMAIL_MODE=console] Verificacion para {recipient}: {url}", flush=True)
