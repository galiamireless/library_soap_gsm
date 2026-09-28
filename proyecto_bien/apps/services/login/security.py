from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash


try:  # pragma: no cover - PyJWT is preferred when available.
    import jwt as _jwt
except ImportError:  # pragma: no cover
    _jwt = None


def _jwt_secret() -> str:
    raw = os.getenv("JWT_SECRET_KEY") or os.getenv("LOGIN_SECRET_KEY") or "change-this-login-secret"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def create_jwt(payload: dict[str, Any] | None = None, *, expires_in: int = 3600, **claims: Any) -> str:
    if _jwt is not None:
        data = dict(payload or {})
        data.update(claims)
        now = int(time.time())
        data.setdefault("iat", now)
        data.setdefault("exp", now + max(1, expires_in))
        return _jwt.encode(data, _jwt_secret(), algorithm="HS256")

    data = dict(payload or {})
    data.update(claims)
    now = int(time.time())
    data.setdefault("iat", now)
    data.setdefault("exp", now + max(1, expires_in))
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _base64url_encode(json.dumps(data, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(_jwt_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{_base64url_encode(signature)}"


def decode_jwt(token: str) -> dict[str, Any]:
    if not token:
        raise ValueError("Token no proporcionado.")

    if _jwt is not None:
        try:
            return _jwt.decode(token, _jwt_secret(), algorithms=["HS256"], options={"require": ["exp", "iat"]})
        except _jwt.InvalidTokenError as exc:  # pragma: no cover - re-raised below.
            raise ValueError("JWT inválido o expirado.") from exc

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("JWT inválido.")
    header_part, payload_part, signature_part = parts
    try:
        header = json.loads(_base64url_decode(header_part).decode("utf-8"))
        payload = json.loads(_base64url_decode(payload_part).decode("utf-8"))
    except (ValueError, TypeError, json.JSONDecodeError):
        raise ValueError("JWT inválido.") from None
    if header.get("alg") != "HS256" or header.get("typ") not in {"JWT", None}:
        raise ValueError("JWT con algoritmo no permitido.")
    if header.get("alg") == "none":
        raise ValueError("JWT con algoritmo no permitido.")
    expected = hmac.new(_jwt_secret().encode("utf-8"), f"{header_part}.{payload_part}".encode("ascii"), hashlib.sha256).digest()
    computed = _base64url_encode(expected)
    if not hmac.compare_digest(signature_part, computed):
        raise ValueError("JWT inválido.")
    if payload.get("exp") is None or int(payload["exp"]) < int(time.time()):
        raise ValueError("JWT expirado.")
    return payload


def get_bearer_token() -> str | None:
    from flask import request

    header = request.headers.get("Authorization", "")
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="scrypt")


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def new_token() -> str:
    return secrets.token_urlsafe(32)
