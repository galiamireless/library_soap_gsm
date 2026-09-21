"""Flask entrypoint for the reorganized library classifier service."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, Response, current_app, request, send_from_directory, url_for
from swagger_ui_bundle import swagger_ui_path
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


SERVICE_DIR = Path(__file__).resolve().parent
SWAGGER_UI_DIRECTORY = Path(swagger_ui_path)
SWAGGER_UI_HTML = """<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Library Classifier API</title>
    <link rel="stylesheet" href="__SWAGGER_CSS_URL__">
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="__SWAGGER_JS_URL__"></script>
    <script>
      window.addEventListener("load", function () {
        window.ui = SwaggerUIBundle({
          url: __SPEC_URL__,
          dom_id: "#swagger-ui",
          deepLinking: true,
          displayRequestDuration: true,
          docExpansion: "list",
          filter: true,
          tryItOutEnabled: true,
          validatorUrl: null
        });
      });
    </script>
  </body>
</html>
"""


def _format() -> str:
    return "json" if request.args.get("format", "xml").strip().lower() == "json" else "xml"


def _response(payload, output_format: str, status: int = 200):
    if output_format == "json":
        return Response(json_codec.dumps(payload), status=status, content_type="application/json; charset=utf-8")
    if not isinstance(payload, (bytes, bytearray, str)):
        payload = xml_codec.serialize_payload(payload)
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
        schema=settings.db_schema,
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
            "routes": ["/health", "/books", "/books/minimal", "/books/concepts", "/soap", "/docs"],
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

    @app.post("/books")
    def create_book():
        data = request.get_json(silent=True) or request.form.to_dict()
        if not data.get("isbn") or not data.get("title"):
            return _error("isbn y title son obligatorios", 400)
        book = get_repository().create_book(data)
        return _response(book, _format(), 201)

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

    @app.get("/docs")
    @app.get("/docs/")
    def swagger_ui():
        html = SWAGGER_UI_HTML.replace(
            "__SPEC_URL__", json.dumps(url_for("openapi_specification"))
        )
        html = html.replace(
            "__SWAGGER_CSS_URL__", url_for("swagger_ui_asset", filename="swagger-ui.css")
        )
        html = html.replace(
            "__SWAGGER_JS_URL__", url_for("swagger_ui_asset", filename="swagger-ui-bundle.js")
        )
        return Response(html, content_type="text/html; charset=utf-8")

    @app.get("/swagger-ui/<path:filename>")
    def swagger_ui_asset(filename: str):
        return send_from_directory(SWAGGER_UI_DIRECTORY, filename, conditional=True)

    @app.get("/openapi.yaml")
    def openapi_specification():
        return send_from_directory(SERVICE_DIR, "openapi.yaml", mimetype="application/yaml", conditional=True)

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
