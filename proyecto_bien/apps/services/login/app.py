from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from email_validator import EmailNotValidError, validate_email
from flask import Flask, Response, request, send_from_directory, session
from werkzeug.exceptions import HTTPException

from .config import Settings
from .mailer import print_verification_email, send_verification_email
from .repository import LoginRepository, UserAlreadyExistsError
from .security import hash_password, new_token, verify_password
from .serialization import json_bytes, xml_bytes


SERVICE_DIR = Path(__file__).resolve().parent
SWAGGER_HTML = """<!doctype html>
<html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Library Login API</title>
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>window.ui = SwaggerUIBundle({url: '/openapi.yaml', dom_id: '#swagger-ui', deepLinking: true, validatorUrl: null});</script>
    </body>
</html>"""


def create_app(test_config: dict | None = None, *, repository=None, mailer=send_verification_email) -> Flask:
    settings = Settings.from_env()
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=settings.secret_key,
        HOST=settings.host,
        PORT=settings.port,
        DEBUG=settings.debug,
        SERVICE_SETTINGS=settings,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    app.extensions["repository"] = repository or LoginRepository(settings.db_config, settings.db_schema)
    app.extensions["mailer"] = print_verification_email if settings.email_mode == "console" else mailer

    def output_format() -> str:
        return "json" if request.args.get("format", "xml").lower() == "json" else "xml"

    def respond(payload, status=200, root="response"):
        if output_format() == "json":
            return Response(json_bytes(payload), status=status, content_type="application/json; charset=utf-8")
        return Response(xml_bytes(payload, root), status=status, content_type="application/xml; charset=utf-8")

    def error(message: str, status: int):
        return respond({"error": message, "status": status}, status, "error")

    def links(*items):
        return {"links": [{"rel": name, "href": url} for name, url in items]}

    def body():
        data = request.get_json(silent=True)
        return data if data is not None else request.form.to_dict()

    def current_user():
        token = session.get("session_token")
        return app.extensions["repository"].get_session_user(token) if token else None

    @app.get("/")
    def index():
        return respond({"service": "library-login", "status": "running", "routes": [
            "/register", "/login", "/logout", "/session", "/verify-email", "/health", "/docs",
        ]})

    @app.get("/health")
    def health():
        app.extensions["repository"].check_health()
        return respond({"service": "library-login", "status": "ok"})

    @app.post("/register")
    def register():
        data = body()
        required = ("nombre", "apellido_paterno", "apellido_materno", "email", "password")
        if any(not str(data.get(key, "")).strip() for key in required):
            return error("Todos los campos son obligatorios.", 400)
        email = str(data["email"]).strip()
        password = str(data["password"])
        try:
            email = validate_email(email, check_deliverability=False).normalized
        except EmailNotValidError:
            return error("El correo electrónico no es válido.", 400)
        if len(password) < 8:
            return error("La contraseña debe tener al menos 8 caracteres.", 400)
        verification_token = new_token()
        try:
            user = app.extensions["repository"].create_user({
                "first_name": str(data["nombre"]).strip(),
                "last_name": str(data["apellido_paterno"]).strip(),
                "maternal_last_name": str(data["apellido_materno"]).strip(),
                "email": email,
                "password_hash": hash_password(password),
                "verification_token": verification_token,
            })
        except UserAlreadyExistsError:
            return error("El correo electrónico ya está registrado.", 409)
        app.extensions["mailer"](app.config["SERVICE_SETTINGS"], email, verification_token)
        user.update({"email_verification_required": True, **links(("self", "/register"), ("login", "/login"))})
        return respond(user, 201)

    @app.get("/verify-email")
    def verify_email():
        user = app.extensions["repository"].verify_email(request.args.get("token", ""))
        if not user:
            return error("El token es inválido o expiró.", 400)
        user.update(links(("self", "/session"), ("login", "/login")))
        return respond(user)

    @app.post("/login")
    def login():
        data = body()
        email = str(data.get("email", "")).strip().lower()
        user = app.extensions["repository"].find_by_email(email)
        if not user or not verify_password(str(data.get("password", "")), user["password_hash"]):
            return error("Credenciales inválidas.", 401)
        if not user["email_verified"]:
            return error("Debes verificar tu correo antes de iniciar sesión.", 403)
        token = new_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=8)
        app.extensions["repository"].create_session(user["user_id"], token, expires_at)
        session.clear()
        session["session_token"] = token
        result = {"message": "Sesión iniciada.", "user": {key: user[key] for key in (
            "user_id", "first_name", "last_name", "maternal_last_name", "email",
        )}, "expires_at": expires_at.isoformat()}
        result.update(links(("self", "/session"), ("logout", "/logout")))
        return respond(result)

    @app.post("/logout")
    def logout():
        token = session.pop("session_token", None)
        if token:
            app.extensions["repository"].delete_session(token)
        session.clear()
        result = {"message": "Sesión cerrada."}
        result.update(links(("login", "/login")))
        return respond(result)

    @app.get("/session")
    def get_session():
        user = current_user()
        if not user:
            return error("No existe una sesión autenticada.", 401)
        result = {"authenticated": True, "user": user}
        result.update(links(("self", "/session"), ("logout", "/logout")))
        return respond(result)

    @app.get("/docs")
    @app.get("/docs/")
    def docs():
        return Response(SWAGGER_HTML, content_type="text/html; charset=utf-8")

    @app.get("/openapi.yaml")
    def openapi():
        return send_from_directory(SERVICE_DIR, "openapi.yaml", mimetype="text/yaml")

    @app.errorhandler(HTTPException)
    def http_error(exception):
        return error(exception.description, exception.code or 500)

    @app.errorhandler(Exception)
    def unexpected_error(exception):
        app.logger.exception("Error inesperado", exc_info=exception)
        return error("Ocurrió un error interno.", 500)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
