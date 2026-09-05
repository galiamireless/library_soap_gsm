import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("SOAP_HOST", "127.0.0.1")
    port: int = int(os.getenv("SOAP_PORT", "5000"))
    debug: bool = os.getenv("SOAP_DEBUG", "false").lower() == "true"
    db_config: dict = None
    wsdl_path: Path = BASE_DIR / "wsdl" / "library-classifier.wsdl"

    def __post_init__(self):
        if self.db_config is None:
            object.__setattr__(self, "db_config", {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "dbname": os.getenv("DB_NAME", "gsm_library_db"),
                "user": os.getenv("DB_USER", "lib_gsm_user"),
                "password": os.getenv("DB_PASSWORD", ""),
            })


settings = Settings()
