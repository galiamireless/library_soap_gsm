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

    @app.post("/bootstrap")
    def bootstrap_admin():
        if request.remote_addr not in {"127.0.0.1", "::1"}:
            return make_error("La configuracion inicial solo se permite desde esta computadora.", 403)
        if STATE["users"]:
            return make_error("La cuenta inicial ya fue configurada.", 409)
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        if not name or not email or len(password) < 8:
            return make_error("name, email y una contraseña de al menos 8 caracteres son obligatorios.", 400)
        user = {"id": 1, "name": name, "email": email, "role_id": 1, "password_hash": hash_password(password)}
        STATE["users"].append(user)
        return jsonify({"message": "Administrador inicial creado.", "user": {key: user[key] for key in ("id", "name", "email", "role_id")}}), 201

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

    @app.get("/users/<int:user_id>")
    @require_jwt({1, 2, 3})
    def get_user(user_id: int):
        user = next((item for item in STATE["users"] if item["id"] == user_id), None)
        if not user:
            return make_error("Usuario no encontrado.", 404)
        return jsonify({"user": {key: user[key] for key in ("id", "name", "email", "role_id")}})

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

    @app.put("/users/<int:user_id>")
    @app.patch("/users/<int:user_id>")
    @require_jwt({1})
    def update_user(user_id: int):
        user = next((item for item in STATE["users"] if item["id"] == user_id), None)
        if not user:
            return make_error("Usuario no encontrado.", 404)
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", user["name"])).strip()
        email = str(data.get("email", user["email"])).strip().lower()
        if not name or not email:
            return make_error("name y email son obligatorios.", 400)
        if any(item["id"] != user_id and item["email"] == email for item in STATE["users"]):
            return make_error("El correo ya pertenece a otro usuario.", 409)
        password = str(data.get("password", ""))
        if password and len(password) < 8:
            return make_error("La contraseña debe tener al menos 8 caracteres.", 400)
        user.update({"name": name, "email": email})
        if password:
            user["password_hash"] = hash_password(password)
        if "role_id" in data:
            role_id = int(data["role_id"])
            if role_id not in STATE["roles"]:
                return make_error("role_id debe ser 1, 2 o 3.", 400)
            user["role_id"] = role_id
        return jsonify({"message": "Usuario actualizado.", "user": {key: user[key] for key in ("id", "name", "email", "role_id")}})

    @app.delete("/users/<int:user_id>")
    @require_jwt({1})
    def delete_user(user_id: int):
        user = next((item for item in STATE["users"] if item["id"] == user_id), None)
        if not user:
            return make_error("Usuario no encontrado.", 404)
        if int(g.jwt_payload.get("user_id", 0)) == user_id:
            return make_error("No puedes eliminar tu propia cuenta administradora.", 409)
        STATE["users"].remove(user)
        return jsonify({"message": "Usuario eliminado.", "id": user_id})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5005, debug=False)
