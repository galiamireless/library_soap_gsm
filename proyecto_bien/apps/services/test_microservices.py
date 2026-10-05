import os
import time

from apps.services.login.security import create_jwt

os.environ.setdefault("JWT_SECRET_KEY", "project-bien-test-secret")

from apps.services.authors.app import create_app as create_authors_app
from apps.services.orders.app import create_app as create_orders_app
from apps.services.payments.app import create_app as create_payments_app
from apps.services.users.app import create_app as create_users_app


def _token(role_id=1, user_id=1):
    return create_jwt({"user_id": user_id, "role_id": role_id}, expires_in=3600)


def test_users_service_requires_jwt_for_admin_actions():
    app = create_users_app({"TESTING": True, "JWT_SECRET_KEY": "project-bien-test-secret"})
    client = app.test_client()

    unauth = client.get("/users")
    assert unauth.status_code == 401

    auth = {"Authorization": f"Bearer {_token(role_id=1, user_id=1)}"}
    create_response = client.post("/users", json={
        "name": "Ana",
        "email": "ana@example.com",
        "password": "StrongPass123!",
        "role_id": 1,
    }, headers=auth)
    assert create_response.status_code == 201
    users = client.get("/users", headers=auth)
    assert users.status_code == 200
    assert users.get_json()["items"][0]["email"] == "ana@example.com"


def test_authors_service_supports_public_reads_and_role_guarded_writes():
    app = create_authors_app({"TESTING": True, "JWT_SECRET_KEY": "project-bien-test-secret"})
    client = app.test_client()

    read_response = client.get("/authors")
    assert read_response.status_code == 200
    assert read_response.get_json()["count"] >= 0

    create_response = client.post(
        "/authors",
        json={"name": "Gabriel García Márquez", "country": "Colombia"},
        headers={"Authorization": f"Bearer {_token(role_id=1, user_id=1)}"},
    )
    assert create_response.status_code == 201
    assert create_response.get_json()["author"]["name"] == "Gabriel García Márquez"


def test_orders_and_payments_flow_updates_status_with_jwt():
    orders_app = create_orders_app({"TESTING": True, "JWT_SECRET_KEY": "project-bien-test-secret"})
    payments_app = create_payments_app({"TESTING": True, "JWT_SECRET_KEY": "project-bien-test-secret"})
    order_client = orders_app.test_client()
    payment_client = payments_app.test_client()
    token = _token(role_id=2, user_id=7)
    headers = {"Authorization": f"Bearer {token}"}

    create_order = order_client.post(
        "/orders",
        json={
            "customer_name": "Carlos",
            "items": [{"book_isbn": "9781234567890", "quantity": 2}],
            "status": "pending",
        },
        headers=headers,
    )
    assert create_order.status_code == 201
    order_id = create_order.get_json()["order"]["id"]

    orders = order_client.get("/orders", headers=headers)
    assert orders.status_code == 200
    assert orders.get_json()["items"][0]["status"] == "pending"

    payment_response = payment_client.post(
        "/payments",
        json={"order_id": order_id, "amount": 300, "method": "card"},
        headers=headers,
    )
    assert payment_response.status_code == 201
    assert payment_response.get_json()["payment"]["status"] == "paid"

    order_after = order_client.get(f"/orders/{order_id}", headers=headers)
    assert order_after.status_code == 200
    assert order_after.get_json()["status"] == "paid"
