"""HTTP routes; SOAP business logic remains in :mod:`soap.service`."""

from __future__ import annotations

from flask import Flask, Response, current_app, request, url_for

from .serialization import serialize


class ApiError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _repository():
    return current_app.extensions["library_repository"]


def register_routes(app: Flask) -> None:
    @app.get("/")
    def index():
        return serialize({
            "service": "library-classifier-soap",
            "status": "running",
            "endpoints": [
                "/health",
                "/books",
                "/books/<isbn>",
                "/books/minimal",
                "/cloud-concepts",
                "/soap",
                "/library-classifier.wsdl",
            ],
            "jsonExample": "/books?format=json",
        })

    @app.get("/health")
    def health():
        _repository().check_health()
        return serialize({"status": "ok", "service": "library-classifier-soap"})

    @app.get("/books")
    @app.get("/books/<isbn>")
    def books(isbn=None):
        result = _repository().list_books(isbn)
        if isbn and not result:
            return serialize({"error": "Book not found", "isbn": isbn}, 404)
        return serialize({"books": result, "count": len(result)})

    @app.get("/books/minimal")
    def minimal_books():
        books_data = _repository().list_books()
        result = [
            {
                "isbn": book["isbn"],
                "title": book["title"],
                "author": book["author"],
                "imageUrl": book["imageUrl"],
            }
            for book in books_data
        ]
        return serialize({"books": result, "count": len(result)})

    @app.get("/cloud-concepts")
    def cloud_concepts():
        concepts = _repository().list_cloud_concepts()
        return serialize({
            "cloudModels": ["IaaS", "PaaS", "SaaS", "FaaS"],
            "concepts": concepts,
            "count": len(concepts),
        })

    @app.get("/library-classifier.wsdl")
    def wsdl():
        with open(current_app.config["WSDL_PATH"], "rb") as wsdl_file:
            payload = wsdl_file.read()
        # Keep generated clients pointed at the host/port that served the WSDL.
        payload = payload.replace(
            b"http://localhost:5000/soap",
            url_for("soap_endpoint", _external=True).encode("utf-8"),
        )
        return Response(payload, content_type="text/xml; charset=utf-8")

    @app.post("/soap")
    def soap_endpoint():
        response_xml, status = current_app.extensions["soap_service"].handle(
            request.get_data(cache=False)
        )
        return Response(
            response_xml,
            status=status,
            content_type="text/xml; charset=utf-8",
        )
