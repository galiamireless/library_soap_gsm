from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


SERVICE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SERVICE_DIR.parents[2]
load_dotenv(PROJECT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    debug: bool
    secret_key: str
    db_config: dict[str, object]
    db_schema: str
    smtp_host: str
    smtp_port: int
    smtp_from: str
    smtp_starttls: bool
    verification_url: str
    email_mode: str

    @classmethod
    def from_env(cls) -> "Settings":
        schema = os.getenv("DB_SCHEMA", "library").strip()
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", schema):
            raise ValueError("DB_SCHEMA solo puede contener identificadores SQL simples.")
        return cls(
            host=os.getenv("LOGIN_HOST", "127.0.0.1"),
            port=int(os.getenv("LOGIN_PORT", "5000")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            secret_key=os.getenv("LOGIN_SECRET_KEY", "change-this-login-secret"),
            db_config={
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "dbname": os.getenv("DB_NAME", "library_classifier_db"),
                "user": os.getenv("DB_USER", "library_classifier_user"),
                "password": os.getenv("DB_PASSWORD", ""),
                "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
                "application_name": os.getenv("DB_APPLICATION_NAME", "library-login"),
            },
            db_schema=schema,
            smtp_host=os.getenv("SMTP_HOST", "127.0.0.1"),
            smtp_port=int(os.getenv("SMTP_PORT", "25")),
            smtp_from=os.getenv("SMTP_FROM", "info@localhost"),
            smtp_starttls=os.getenv("SMTP_STARTTLS", "false").lower() == "true",
            verification_url=os.getenv("LOGIN_VERIFICATION_URL", "http://127.0.0.1:5000/verify-email"),
            email_mode=os.getenv("LOGIN_EMAIL_MODE", "smtp").lower(),
        )
