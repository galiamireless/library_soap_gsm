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
        return jsonify({"service": "orders", "status": "running", "routes": ["/orders", "/orders/<id>"]})

    @app.get("/health")
    def health():
        return jsonify({"service": "orders", "status": "ok"})

    @app.get("/orders")
    @require_jwt({1, 2, 3})
    def list_orders():
        items = list(STATE["orders"].values())
        return jsonify({"count": len(items), "items": items})

    @app.get("/orders/<int:order_id>")
    @require_jwt({1, 2, 3})
    def get_order(order_id: int):
        order = STATE["orders"].get(order_id)
        if not order:
            return make_error("Pedido no encontrado.", 404)
        return jsonify(order)

    @app.post("/orders")
    @require_jwt({1, 2, 3})
    def create_order():
        data = request.get_json(silent=True) or request.form.to_dict()
        customer_name = str(data.get("customer_name", "")).strip()
        items = data.get("items") or []
        if not customer_name or not items:
            return make_error("customer_name y items son obligatorios.", 400)
        order_id = max(STATE["orders"].keys(), default=0) + 1
        order = {
            "id": order_id,
            "customer_name": customer_name,
            "items": items,
            "status": str(data.get("status", "pending")),
            "total": sum(float(item.get("price", 0) or 0) * float(item.get("quantity", 0) or 0) for item in items),
        }
        STATE["orders"][order_id] = order
        return jsonify({"message": "Pedido creado.", "order": order}), 201

    @app.patch("/orders/<int:order_id>")
    @require_jwt({1, 2})
    def update_order_status(order_id: int):
        order = STATE["orders"].get(order_id)
        if not order:
            return make_error("Pedido no encontrado.", 404)
        status = str(request.get_json(silent=True) or {}).get("status", order["status"])
        order["status"] = status
        return jsonify(order)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5007, debug=False)
