import base64
import hashlib
import hmac
import os
from xml.etree import ElementTree as ET

WSSE_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"pbkdf2_sha256$120000${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(salt), int(iterations)
        )
        return hmac.compare_digest(base64.b64encode(digest).decode(), expected)
    except (ValueError, TypeError):
        return False


def read_username_token(header: ET.Element) -> tuple[str, str] | None:
    token = header.find(f".//{{{WSSE_NS}}}UsernameToken")
    if token is None:
        return None
    username = token.findtext(f"{{{WSSE_NS}}}Username")
    password = token.findtext(f"{{{WSSE_NS}}}Password")
    if not username or not password:
        return None
    return username, password


def configured_users() -> dict[str, str]:
    users: dict[str, str] = {}
    raw = os.getenv("SOAP_USER_HASHES", "")
    for entry in raw.split(","):
        if ":" in entry:
            username, encoded = entry.split(":", 1)
            users[username.strip()] = encoded.strip()
    return users
