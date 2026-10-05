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
        return jsonify({"service": "payments", "status": "running", "routes": ["/payments", "/payments/<id>"]})

    @app.get("/health")
    def health():
        return jsonify({"service": "payments", "status": "ok"})

    @app.get("/payments")
    @require_jwt({1, 2, 3})
    def list_payments():
        return jsonify({"count": len(STATE["payments"]), "items": STATE["payments"]})

    @app.post("/payments")
    @require_jwt({1, 2, 3})
    def create_payment():
        data = request.get_json(silent=True) or request.form.to_dict()
        order_id = int(data.get("order_id", 0) or 0)
        amount = float(data.get("amount", 0) or 0)
        method = str(data.get("method", "card")).strip() or "card"
        if order_id <= 0 or amount <= 0:
            return make_error("order_id y amount son obligatorios.", 400)
        if order_id in STATE["orders"]:
            STATE["orders"][order_id]["status"] = "paid"
        payment = {
            "id": len(STATE["payments"]) + 1,
            "order_id": order_id,
            "amount": amount,
            "method": method,
            "status": "paid",
        }
        STATE["payments"].append(payment)
        return jsonify({"message": "Pago registrado.", "payment": payment}), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5008, debug=False)
