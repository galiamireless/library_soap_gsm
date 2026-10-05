from __future__ import annotations

import os
from functools import wraps
from typing import Any

from flask import g, jsonify, request

from apps.services.login.security import decode_jwt, get_bearer_token


def get_service_secret() -> str:
    return os.getenv("JWT_SECRET_KEY") or os.getenv("LOGIN_SECRET_KEY") or "project-bien-default-secret"


def require_jwt(required_roles: set[int] | None = None, *, deny_if_missing: bool = True):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = get_bearer_token()
            if not token:
                return jsonify({"error": "Authorization Bearer requerido.", "status": 401}), 401
            try:
                payload = decode_jwt(token)
            except ValueError:
                return jsonify({"error": "JWT inválido o expirado.", "status": 401}), 401

            role_id = int(payload.get("role_id", 0) or 0)
            if required_roles is not None and role_id not in required_roles:
                return jsonify({"error": "No tienes permisos suficientes.", "status": 403}), 403

            g.jwt_payload = payload
            return func(*args, **kwargs)

        return wrapper

    return decorator


def make_error(message: str, status: int):
    return jsonify({"error": message, "status": status}), status


def json_response(payload: Any, status: int = 200):
    return jsonify(payload), status
