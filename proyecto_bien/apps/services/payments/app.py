from __future__ import annotations

import os
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request

from apps.services.common import make_error, require_jwt
from apps.services.login.security import create_jwt
from apps.services.shared_state import STATE


def update_order_status(order_id: int, status: str, *, testing: bool = False) -> bool:
    if testing:
        order = STATE["orders"].get(order_id)
        if not order:
            return False
        order["status"] = status
        return True

    orders_url = os.getenv("ORDERS_SERVICE_URL", "http://127.0.0.1:5007").rstrip("/")
    token = create_jwt({"user_id": 0, "role_id": 2, "service": "payments"}, expires_in=60)
    payload = json.dumps({"status": status}).encode("utf-8")
    req = Request(f"{orders_url}/orders/{order_id}", data=payload, method="PATCH")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=4) as response:
            return 200 <= response.status < 300
    except (HTTPError, URLError, TimeoutError, OSError):
        return False


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

    @app.get("/payments/<int:payment_id>")
    @require_jwt({1, 2, 3})
    def get_payment(payment_id: int):
        payment = next((item for item in STATE["payments"] if item["id"] == payment_id), None)
        if not payment:
            return make_error("Pago no encontrado.", 404)
        return jsonify({"payment": payment})

    @app.post("/payments")
    @require_jwt({1, 2, 3})
    def create_payment():
        data = request.get_json(silent=True) or request.form.to_dict()
        order_id = int(data.get("order_id", 0) or 0)
        amount = float(data.get("amount", 0) or 0)
        method = str(data.get("method", "card")).strip() or "card"
        if order_id <= 0 or amount <= 0:
            return make_error("order_id y amount son obligatorios.", 400)
        if not update_order_status(order_id, "paid", testing=app.config.get("TESTING", False)):
            return make_error("No se pudo actualizar el pedido; verifica que exista y que Orders esté disponible.", 502)
        payment = {
            "id": len(STATE["payments"]) + 1,
            "order_id": order_id,
            "amount": amount,
            "method": method,
            "status": "paid",
        }
        STATE["payments"].append(payment)
        return jsonify({"message": "Pago registrado.", "payment": payment}), 201

    @app.put("/payments/<int:payment_id>")
    @app.patch("/payments/<int:payment_id>")
    @require_jwt({1, 2})
    def update_payment(payment_id: int):
        payment = next((item for item in STATE["payments"] if item["id"] == payment_id), None)
        if not payment:
            return make_error("Pago no encontrado.", 404)
        data = request.get_json(silent=True) or {}
        amount = float(data.get("amount", payment["amount"]) or 0)
        if amount <= 0:
            return make_error("amount debe ser mayor que cero.", 400)
        payment.update({"amount": amount, "method": str(data.get("method", payment["method"])).strip() or "card"})
        return jsonify({"message": "Pago actualizado.", "payment": payment})

    @app.delete("/payments/<int:payment_id>")
    @require_jwt({1, 2})
    def delete_payment(payment_id: int):
        payment = next((item for item in STATE["payments"] if item["id"] == payment_id), None)
        if not payment:
            return make_error("Pago no encontrado.", 404)
        if payment["status"] == "paid" and not update_order_status(payment["order_id"], "pending", testing=app.config.get("TESTING", False)):
            return make_error("No se pudo restaurar el estado del pedido en Orders.", 502)
        STATE["payments"].remove(payment)
        return jsonify({"message": "Pago eliminado.", "id": payment_id})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5008, debug=False)
