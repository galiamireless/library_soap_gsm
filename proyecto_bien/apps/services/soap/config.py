"""Runtime configuration for the SOAP service."""

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
    max_xml_bytes: int
    db_config: dict[str, object]
    db_schema: str
    pool_min_size: int
    pool_max_size: int
    pool_timeout: float
    wsdl_path: Path = SERVICE_DIR / "library-classifier.wsdl"

    @classmethod
    def from_env(cls) -> "Settings":
        db_schema = os.getenv("DB_SCHEMA", "library").strip()
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", db_schema):
            raise ValueError("DB_SCHEMA solo puede contener identificadores SQL simples.")
        return cls(
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "5001")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            max_xml_bytes=int(os.getenv("MAX_XML_BYTES", str(1024 * 1024))),
            db_config={
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "dbname": os.getenv("DB_NAME", "library_classifier_db"),
                "user": os.getenv("DB_USER", "library_classifier_user"),
                "password": os.getenv("DB_PASSWORD", ""),
                "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
                "application_name": os.getenv("DB_APPLICATION_NAME", "library-classifier"),
            },
            db_schema=db_schema,
            pool_min_size=int(os.getenv("DB_POOL_MIN_SIZE", "1")),
            pool_max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
            pool_timeout=float(os.getenv("DB_POOL_TIMEOUT", "5")),
        )


settings = Settings.from_env()
