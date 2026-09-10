"""Flask entrypoint for the reorganized library classifier service."""

from __future__ import annotations

from flask import Flask, Response, current_app, request, url_for
from werkzeug.exceptions import HTTPException

try:
    from . import json_codec, xml_codec
    from .config import Settings
    from .repository import LibraryRepository
    from .soap_service import SoapService
except ImportError:  # Allows ``python app.py`` from this directory too.
    import json_codec
    import xml_codec
    from config import Settings
    from repository import LibraryRepository
    from soap_service import SoapService


def _format() -> str:
    return "json" if request.args.get("format", "xml").strip().lower() == "json" else "xml"


def _response(payload, output_format: str, status: int = 200):
    if output_format == "json":
        return Response(json_codec.dumps(payload), status=status, content_type="application/json; charset=utf-8")
    return Response(payload, status=status, content_type="application/xml; charset=utf-8")


def _error(message: str, status: int):
    if _format() == "json":
        return _response({"error": message, "status": status}, "json", status)
    return _response(xml_codec.serialize_error(message, status), "xml", status)


def create_app(test_config: dict | None = None, *, repository=None) -> Flask:
    settings = Settings.from_env()
    app = Flask(__name__)
    app.config.from_mapping(
        HOST=settings.host,
        PORT=settings.port,
        DEBUG=settings.debug,
        MAX_CONTENT_LENGTH=settings.max_xml_bytes,
        WSDL_PATH=str(settings.wsdl_path),
    )
    if test_config:
        app.config.update(test_config)

    repo = repository or LibraryRepository(
        settings.db_config,
        pool_settings={
            "db_config": settings.db_config,
            "min_size": settings.pool_min_size,
            "max_size": settings.pool_max_size,
            "timeout": settings.pool_timeout,
        },
    )
    app.extensions["repository"] = repo
    app.extensions["soap_service"] = SoapService(repo)

    def get_repository():
        return current_app.extensions["repository"]

    @app.get("/")
    def index():
        return _response({
            "service": "library-classifier",
            "status": "running",
            "routes": ["/health", "/books", "/books/minimal", "/books/concepts", "/soap"],
        }, _format())

    @app.get("/health")
    def health():
        get_repository().check_health()
        return _response({"service": "library-classifier", "status": "ok"}, _format())

    @app.get("/books")
    @app.get("/books/<isbn>")
    def books(isbn: str | None = None):
        result = get_repository().list_books(isbn)
        if isbn and not result:
            return _error("Book not found", 404)
        if _format() == "json":
            return _response({"books": result, "count": len(result)}, "json")
        return _response(xml_codec.serialize_library(result), "xml")

    @app.get("/books/minimal")
    def minimal_books():
        result = get_repository().list_minimal_books()
        if _format() == "json":
            return _response({
                "books": [{key: book.get(key) for key in ("isbn", "title", "author", "imageUrl")} for book in result],
                "count": len(result),
            }, "json")
        return _response(xml_codec.serialize_minimal(result), "xml")

    @app.get("/books/concepts")
    @app.get("/books/concepts/")
    @app.get("/cloud-concepts")
    def cloud_concepts():
        result = get_repository().list_cloud_concepts()
        if _format() == "json":
            return _response({"cloudModels": ["IaaS", "PaaS", "SaaS", "FaaS"], "concepts": result, "count": len(result)}, "json")
        return _response(xml_codec.serialize_concepts(result), "xml")

    @app.get("/library-classifier.wsdl")
    def wsdl():
        with open(app.config["WSDL_PATH"], "rb") as handle:
            payload = handle.read()
        payload = payload.replace(
            b"http://localhost:5001/soap",
            url_for("soap_endpoint", _external=True).encode("utf-8"),
        )
        return Response(payload, content_type="text/xml; charset=utf-8")

    @app.post("/soap")
    def soap_endpoint():
        payload, status = current_app.extensions["soap_service"].handle(request.get_data(cache=False))
        return Response(payload, status=status, content_type="text/xml; charset=utf-8")

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException):
        return _error(error.description, error.code or 500)

    @app.errorhandler(Exception)
    def unexpected_error(error: Exception):
        app.logger.exception("Error inesperado", exc_info=error)
        return _error("Ocurrió un error interno.", 500)

    try:
        import psycopg
        from psycopg_pool import PoolTimeout
    except ImportError:  # pragma: no cover
        psycopg = None
        PoolTimeout = None

    if psycopg is not None:
        @app.errorhandler(psycopg.Error)
        def database_error(error):
            app.logger.exception("Error de PostgreSQL", exc_info=error)
            return _error("No fue posible acceder a PostgreSQL.", 503)

    if PoolTimeout is not None:
        @app.errorhandler(PoolTimeout)
        def pool_timeout(error):
            app.logger.warning("Tiempo de espera agotado esperando una conexión")
            return _error("No hay conexiones disponibles en este momento.", 503)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
