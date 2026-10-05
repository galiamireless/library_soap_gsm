import os
import threading

from werkzeug.serving import make_server

from apps.services.login.security import create_jwt

os.environ.setdefault("JWT_SECRET_KEY", "project-bien-test-secret")

from apps.services.authors.app import create_app as create_authors_app
from apps.services.orders.app import create_app as create_orders_app
from apps.services.payments.app import create_app as create_payments_app
from apps.services.users.app import create_app as create_users_app
from apps.services.shared_state import reset_state


def _token(role_id=1, user_id=1):
    return create_jwt({"user_id": user_id, "role_id": role_id}, expires_in=3600)


def test_users_service_requires_jwt_for_admin_actions():
    reset_state()
    app = create_users_app({"TESTING": True, "JWT_SECRET_KEY": "project-bien-test-secret"})
    client = app.test_client()

    unauth = client.get("/users")
    assert unauth.status_code == 401

    bootstrap = client.post("/bootstrap", json={
        "name": "Admin local", "email": "admin@example.test", "password": "AdminPass123!",
    })
    assert bootstrap.status_code == 201
    login = client.post("/login", json={"email": "admin@example.test", "password": "AdminPass123!"})
    assert login.status_code == 200
    auth = {"Authorization": f"Bearer {login.get_json()['token']}"}

    create_response = client.post("/users", json={
        "name": "Ana",
        "email": "ana@example.com",
        "password": "StrongPass123!",
        "role_id": 1,
    }, headers=auth)
    assert create_response.status_code == 201
    user_id = create_response.get_json()["user"]["id"]
    users = client.get("/users", headers=auth)
    assert users.status_code == 200
    assert next(item for item in users.get_json()["items"] if item["id"] == user_id)["email"] == "ana@example.com"
    assert client.get(f"/users/{user_id}", headers=auth).status_code == 200
    updated = client.patch(f"/users/{user_id}", json={"name": "Ana Editada"}, headers=auth)
    assert updated.get_json()["user"]["name"] == "Ana Editada"
    assert client.delete(f"/users/{user_id}", headers=auth).status_code == 200


def test_authors_service_supports_public_reads_and_role_guarded_writes():
    reset_state()
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
    author_id = create_response.get_json()["author"]["id"]
    assert client.get(f"/authors/{author_id}").status_code == 200
    updated = client.patch(f"/authors/{author_id}", json={"name": "Gabriel Editado"}, headers={"Authorization": f"Bearer {_token()}"})
    assert updated.get_json()["author"]["name"] == "Gabriel Editado"
    deleted = client.delete(f"/authors/{author_id}", headers={"Authorization": f"Bearer {_token()}"})
    assert deleted.status_code == 200


def test_orders_and_payments_flow_updates_status_with_jwt():
    reset_state()
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

    update_order = order_client.patch(f"/orders/{order_id}", json={"customer_name": "Carlos Editado"}, headers=headers)
    assert update_order.get_json()["order"]["customer_name"] == "Carlos Editado"

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
    payment_id = payment_response.get_json()["payment"]["id"]
    assert payment_client.get(f"/payments/{payment_id}", headers=headers).status_code == 200
    payment_update = payment_client.patch(f"/payments/{payment_id}", json={"method": "transfer", "amount": 350}, headers=headers)
    assert payment_update.get_json()["payment"]["method"] == "transfer"

    order_after = order_client.get(f"/orders/{order_id}", headers=headers)
    assert order_after.status_code == 200
    assert order_after.get_json()["status"] == "paid"
    assert payment_client.delete(f"/payments/{payment_id}", headers=headers).status_code == 200
    assert order_client.delete(f"/orders/{order_id}", headers=headers).status_code == 200


def test_payments_updates_orders_across_http_services(monkeypatch):
    reset_state()
    orders_app = create_orders_app({"TESTING": True, "JWT_SECRET_KEY": "project-bien-test-secret"})
    server = make_server("127.0.0.1", 0, orders_app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("ORDERS_SERVICE_URL", f"http://127.0.0.1:{server.server_port}")
    token = _token(role_id=2, user_id=10)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        order_response = orders_app.test_client().post("/orders", json={
            "customer_name": "HTTP test",
            "items": [{"book_isbn": "9786070001001", "quantity": 1, "price": 10}],
        }, headers=headers)
        order_id = order_response.get_json()["order"]["id"]
        payments_app = create_payments_app({"TESTING": False, "JWT_SECRET_KEY": "project-bien-test-secret"})
        payment_response = payments_app.test_client().post("/payments", json={
            "order_id": order_id, "amount": 10, "method": "card",
        }, headers=headers)

        assert payment_response.status_code == 201
        order_after = orders_app.test_client().get(f"/orders/{order_id}", headers=headers)
        assert order_after.get_json()["status"] == "paid"
    finally:
        server.shutdown()
        server.server_close()
