from datetime import datetime, timezone

from apps.services.login.app import create_app
from apps.services.login.security import create_jwt, hash_password


class FakeRepository:
    def __init__(self):
        self.user = None
        self.users = []
        self.sessions = {}

    def check_health(self):
        return True

    def create_user(self, data):
        self.user = {
            "user_id": 1,
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "maternal_last_name": data["maternal_last_name"],
            "email": data["email"],
            "email_verified": False,
            "role_id": data.get("role_id", 3),
            "created_at": datetime.now(timezone.utc),
            "verification_token": data["verification_token"],
            "password_hash": data["password_hash"],
        }
        self.users.append(self.user)
        return {key: self.user[key] for key in (
            "user_id", "first_name", "last_name", "maternal_last_name", "email",
            "email_verified", "role_id", "created_at",
        )}

    def verify_email(self, token):
        if self.user and self.user["verification_token"] == token:
            self.user["email_verified"] = True
            return {key: self.user[key] for key in (
                "user_id", "first_name", "last_name", "maternal_last_name", "email",
                "email_verified", "created_at",
            )}
        return None

    def find_by_email(self, email):
        return next((user for user in self.users if user["email"] == email), None)

    def list_users(self):
        return [{key: user[key] for key in ("user_id", "first_name", "last_name", "maternal_last_name", "email", "email_verified", "role_id", "created_at")} for user in self.users]

    def get_user(self, user_id):
        user = next((item for item in self.users if item["user_id"] == user_id), None)
        return {key: user[key] for key in ("user_id", "first_name", "last_name", "maternal_last_name", "email", "email_verified", "role_id", "created_at")} if user else None

    def update_user(self, user_id, data):
        user = next((item for item in self.users if item["user_id"] == user_id), None)
        if not user:
            return None
        user.update(data)
        return self.get_user(user_id)

    def delete_user(self, user_id):
        user = next((item for item in self.users if item["user_id"] == user_id), None)
        if not user:
            return False
        self.users.remove(user)
        return True

    def create_session(self, user_id, token, expires_at):
        self.sessions[token] = user_id

    def get_session_user(self, token):
        if token in self.sessions and self.user:
            return {key: self.user[key] for key in (
                "user_id", "first_name", "last_name", "maternal_last_name", "email",
                "email_verified",
            )}
        return None

    def delete_session(self, token):
        self.sessions.pop(token, None)


def build_app():
    repository = FakeRepository()
    sent = []

    def fake_mailer(settings, recipient, token):
        sent.append((recipient, token))

    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"}, repository=repository, mailer=fake_mailer)
    return app, repository, sent


def registration_payload():
    return {
        "nombre": "Ana", "apellido_paterno": "Lopez", "apellido_materno": "Diaz",
        "email": "ana@example.com", "password": "Correcta123!",
    }


def test_register_defaults_to_xml_and_sends_verification_email():
    app, _, sent = build_app()
    response = app.test_client().post("/register", json=registration_payload())

    assert response.status_code == 201
    assert response.mimetype == "application/xml"
    assert sent[0][0] == "ana@example.com"
    assert b"email_verification_required" in response.data


def test_login_requires_verified_email_then_session_and_logout_work():
    app, repository, sent = build_app()
    client = app.test_client()
    client.post("/register?format=json", json=registration_payload())

    blocked = client.post("/login?format=json", json={"email": "ana@example.com", "password": "Correcta123!"})
    assert blocked.status_code == 403

    client.get(f"/verify-email?format=json&token={sent[0][1]}")
    logged_in = client.post("/login?format=json", json={"email": "ana@example.com", "password": "Correcta123!"})
    assert logged_in.status_code == 200
    assert logged_in.get_json()["user"]["email"] == "ana@example.com"
    assert client.get("/session?format=json").get_json()["authenticated"] is True

    client.post("/logout?format=json")
    assert client.get("/session?format=json").status_code == 401
    assert repository.sessions == {}


def test_invalid_email_and_wrong_password_are_rejected():
    app, _, _ = build_app()
    client = app.test_client()
    assert client.post("/register?format=json", json={**registration_payload(), "email": "bad"}).status_code == 400
    client.post("/register?format=json", json=registration_payload())
    app.extensions["repository"].user["email_verified"] = True
    response = client.post("/login?format=json", json={"email": "ana@example.com", "password": "wrong"})
    assert response.status_code == 401


def test_admin_account_crud_requires_admin_jwt(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "login-test-jwt-secret")
    app, _, sent = build_app()
    client = app.test_client()
    assert client.get("/admin/users?format=json").status_code == 401
    token = create_jwt({"user_id": 1, "role_id": 1}, expires_in=3600)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/admin/users?format=json", json={
        "first_name": "Luis", "last_name": "Vega", "maternal_last_name": "Rios",
        "email": "luis@example.com", "password": "Correcta123!", "role_id": 2,
    }, headers=headers)
    assert created.status_code == 201
    user_id = created.get_json()["user"]["user_id"]
    assert sent[-1][0] == "luis@example.com"
    assert client.get("/admin/users?format=json", headers=headers).get_json()["count"] == 1
    updated = client.patch(f"/admin/users/{user_id}?format=json", json={"role_id": 3}, headers=headers)
    assert updated.get_json()["user"]["role_id"] == 3
    assert client.delete(f"/admin/users/{user_id}?format=json", headers=headers).status_code == 200
