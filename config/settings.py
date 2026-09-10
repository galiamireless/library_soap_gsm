import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    debug: bool
    db_config: dict
    wsdl_path: Path
    max_content_length: int
    db_pool_min_size: int
    db_pool_max_size: int
    db_pool_timeout: float

    @classmethod
    def from_env(cls) -> "Settings":
        """Read settings at app creation time instead of import time."""
        return cls(
            host=os.getenv("SOAP_HOST", "127.0.0.1"),
            port=int(os.getenv("SOAP_PORT", "5000")),
            debug=os.getenv("SOAP_DEBUG", "false").lower() == "true",
            db_config={
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "dbname": os.getenv("DB_NAME", "gsm_library_db"),
                "user": os.getenv("DB_USER", "lib_gsm_user"),
                "password": os.getenv("DB_PASSWORD", ""),
                "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
                "application_name": os.getenv("DB_APPLICATION_NAME", "library-soap"),
            },
            wsdl_path=BASE_DIR / "wsdl" / "library-classifier.wsdl",
            max_content_length=int(os.getenv("MAX_XML_BYTES", str(1024 * 1024))),
            db_pool_min_size=int(os.getenv("DB_POOL_MIN_SIZE", "1")),
            db_pool_max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
            db_pool_timeout=float(os.getenv("DB_POOL_TIMEOUT", "5")),
        )


settings = Settings.from_env()
