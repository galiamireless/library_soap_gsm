from __future__ import annotations

import os

from flask import Flask, g, jsonify, request

from apps.services.common import make_error, require_jwt
from apps.services.login.security import hash_password, verify_password, create_jwt
from apps.services.shared_state import STATE


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("JWT_SECRET_KEY", "project-bien-default-secret"),
    )
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        return jsonify({"service": "users", "status": "running", "routes": ["/users", "/login", "/health"]})

    @app.get("/health")
    def health():
        return jsonify({"service": "users", "status": "ok"})

    @app.post("/login")
    def login():
        data = request.get_json(silent=True) or request.form.to_dict()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        user = next((item for item in STATE["users"] if item["email"] == email), None)
        if not user or not verify_password(password, user["password_hash"]):
            return make_error("Credenciales inválidas.", 401)
        token = create_jwt({
            "user_id": user["id"],
            "email": user["email"],
            "role_id": user["role_id"],
        }, expires_in=20 * 60)
        return jsonify({"message": "Sesión iniciada.", "token": token, "token_type": "Bearer", "expires_in": 20 * 60, "user": {"id": user["id"], "email": user["email"], "role_id": user["role_id"]}}), 200

    @app.get("/users")
    @require_jwt({1, 2, 3})
    def list_users():
        return jsonify({"count": len(STATE["users"]), "items": [
            {"id": item["id"], "name": item["name"], "email": item["email"], "role_id": item["role_id"]}
            for item in STATE["users"]
        ]})

    @app.post("/users")
    @require_jwt({1})
    def create_user():
        data = request.get_json(silent=True) or request.form.to_dict()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        if not email or not password or not data.get("name"):
            return make_error("name, email y password son obligatorios.", 400)
        if any(item["email"] == email for item in STATE["users"]):
            return make_error("El usuario ya existe.", 409)
        if len(password) < 8:
            return make_error("La contraseña debe tener al menos 8 caracteres.", 400)
        user_id = max((item["id"] for item in STATE["users"]), default=0) + 1
        user = {
            "id": user_id,
            "name": str(data["name"]).strip(),
            "email": email,
            "role_id": int(data.get("role_id", 3) or 3),
            "password_hash": hash_password(password),
        }
        STATE["users"].append(user)
        return jsonify({"message": "Usuario creado.", "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role_id": user["role_id"]}}), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5005, debug=False)
