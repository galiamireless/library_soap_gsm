from __future__ import annotations

import os

from flask import Flask, jsonify, request

from apps.services.common import make_error, require_jwt
from apps.services.shared_state import STATE


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=os.getenv("JWT_SECRET_KEY", "project-bien-default-secret"))
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        return jsonify({"service": "authors", "status": "running", "routes": ["/authors", "/authors/<id>"]})

    @app.get("/health")
    def health():
        return jsonify({"service": "authors", "status": "ok"})

    @app.get("/authors")
    def list_authors():
        return jsonify({"count": len(STATE["authors"]), "items": STATE["authors"]})

    @app.get("/authors/<int:author_id>")
    def get_author(author_id: int):
        author = next((item for item in STATE["authors"] if item["id"] == author_id), None)
        if not author:
            return make_error("Autor no encontrado.", 404)
        return jsonify({"author": author})

    @app.put("/authors/<int:author_id>")
    @app.patch("/authors/<int:author_id>")
    @require_jwt({1, 2})
    def update_author(author_id: int):
        author = next((item for item in STATE["authors"] if item["id"] == author_id), None)
        if not author:
            return make_error("Autor no encontrado.", 404)
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", author["name"])).strip()
        if not name:
            return make_error("El nombre del autor es obligatorio.", 400)
        author.update({"name": name, "country": str(data.get("country", author.get("country", ""))).strip()})
        return jsonify({"message": "Autor actualizado.", "author": author})

    @app.delete("/authors/<int:author_id>")
    @require_jwt({1, 2})
    def delete_author(author_id: int):
        author = next((item for item in STATE["authors"] if item["id"] == author_id), None)
        if not author:
            return make_error("Autor no encontrado.", 404)
        STATE["authors"].remove(author)
        return jsonify({"message": "Autor eliminado.", "id": author_id})

    @app.post("/authors")
    @require_jwt({1, 2})
    def create_author():
        data = request.get_json(silent=True) or request.form.to_dict()
        name = str(data.get("name", "")).strip()
        if not name:
            return make_error("El nombre del autor es obligatorio.", 400)
        author_id = max((item["id"] for item in STATE["authors"]), default=0) + 1
        author = {"id": author_id, "name": name, "country": str(data.get("country", "")).strip()}
        STATE["authors"].append(author)
        return jsonify({"message": "Autor creado.", "author": author}), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5006, debug=False)
