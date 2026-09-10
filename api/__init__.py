"""HTTP application factory for the library classifier service."""

from __future__ import annotations

from typing import Any

from flask import Flask
from werkzeug.exceptions import HTTPException

from config.settings import Settings
from db.repository import DatabaseRepository
from soap.service import SoapService

from .routes import ApiError, register_routes


def create_app(
    test_config: dict[str, Any] | None = None,
    *,
    repository: DatabaseRepository | None = None,
) -> Flask:
    """Create an isolated Flask application.

    The repository can be injected by tests or by an embedding application.
    Production code gets a repository backed by a PostgreSQL connection pool.
    """
    settings = Settings.from_env()
    app = Flask(__name__)
    app.config.from_mapping(
        HOST=settings.host,
        PORT=settings.port,
        DEBUG=settings.debug,
        MAX_CONTENT_LENGTH=settings.max_content_length,
        WSDL_PATH=str(settings.wsdl_path),
    )
    if test_config:
        app.config.update(test_config)

    service_repository = repository or DatabaseRepository(
        settings.db_config,
        pool_settings={
            "min_size": settings.db_pool_min_size,
            "max_size": settings.db_pool_max_size,
            "timeout": settings.db_pool_timeout,
        },
    )
    app.extensions["library_repository"] = service_repository
    app.extensions["soap_service"] = SoapService(service_repository)

    register_routes(app)

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return error_response(app, error.status_code, error.message)

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        messages = {
            404: "El recurso solicitado no existe.",
            405: "El método HTTP no está permitido para este recurso.",
            413: "El documento XML excede el tamaño permitido.",
        }
        return error_response(app, error.code or 500, messages.get(error.code, error.description))

    try:
        import psycopg
    except ImportError:  # pragma: no cover - dependencies are declared in requirements.txt
        psycopg = None
    try:
        from psycopg_pool import PoolTimeout
    except ImportError:  # pragma: no cover - dependencies are declared in requirements.txt
        PoolTimeout = None

    if psycopg is not None:
        from psycopg import errors

        @app.errorhandler(psycopg.Error)
        def handle_database_error(error):
            app.logger.exception("Error de PostgreSQL", exc_info=error)
            if isinstance(error, errors.UniqueViolation):
                status, message = 409, "El registro ya existe."
            elif isinstance(error, (errors.CheckViolation, errors.NotNullViolation, errors.DataError, errors.ForeignKeyViolation)):
                status, message = 422, "Los datos no cumplen las restricciones de PostgreSQL."
            elif isinstance(error, (errors.OperationalError, errors.InterfaceError)):
                status, message = 503, "No fue posible acceder a PostgreSQL."
            else:
                status, message = 500, "Ocurrió un error al consultar PostgreSQL."
            return error_response(app, status, message)

    if PoolTimeout is not None:
        @app.errorhandler(PoolTimeout)
        def handle_pool_timeout(error):
            app.logger.warning("El pool de PostgreSQL agotó su tiempo de espera: %s", error)
            return error_response(app, 503, "El servicio está ocupado; inténtelo de nuevo.")

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Error inesperado", exc_info=error)
        return error_response(app, 500, "Ocurrió un error interno.")

    return app


def error_response(app: Flask, status: int, message: str):
    from .serialization import serialize_error_response

    return serialize_error_response(message, status)


app = create_app()
