"""Flask entry point for the independent library SOAP service."""
from datetime import date, datetime
from decimal import Decimal
from xml.etree import ElementTree as ET

from flask import Flask, Response, jsonify, request

from config.settings import settings
from db.repository import DatabaseRepository
from soap.service import SoapService

app = Flask(__name__)
repository = DatabaseRepository(settings.db_config)
service = SoapService(repository)


def response_format() -> str:
    return "json" if request.args.get("format", "xml").lower() == "json" else "xml"


def xml_value(parent: ET.Element, key: str, value) -> None:
    if isinstance(value, list):
        container = ET.SubElement(parent, key)
        for item in value:
            xml_value(container, "item", item)
        return
    element = ET.SubElement(parent, key)
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            xml_value(element, child_key, child_value)
    elif value is not None:
        element.text = str(value)


def json_safe(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    return value


def serialize(data, status: int = 200):
    data = json_safe(data)
    if response_format() == "json":
        return jsonify(data), status
    root = ET.Element("response")
    if isinstance(data, dict):
        for key, value in data.items():
            xml_value(root, key, value)
    else:
        xml_value(root, "items", data)
    return Response(ET.tostring(root, encoding="unicode"), status=status, mimetype="application/xml")


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
    try:
        repository.check_health()
        return serialize({"status": "ok", "service": "library-classifier-soap"})
    except Exception:
        return serialize({"status": "unavailable", "service": "library-classifier-soap"}, 503)


@app.get("/books")
@app.get("/books/<isbn>")
def books(isbn=None):
    result = repository.list_books(isbn)
    if isbn and not result:
        return serialize({"error": "Book not found", "isbn": isbn}, 404)
    return serialize({"books": result, "count": len(result)})


@app.get("/books/minimal")
def minimal_books():
    books_data = repository.list_books()
    result = [
        {"isbn": book["isbn"], "title": book["title"],
         "author": book["author"], "imageUrl": book["imageUrl"]}
        for book in books_data
    ]
    return serialize({"books": result, "count": len(result)})


@app.get("/cloud-concepts")
def cloud_concepts():
    concepts = repository.list_cloud_concepts()
    return serialize({
        "cloudModels": ["IaaS", "PaaS", "SaaS", "FaaS"],
        "concepts": concepts,
        "count": len(concepts),
    })


@app.get("/library-classifier.wsdl")
def wsdl():
    with open(settings.wsdl_path, "rb") as wsdl_file:
        return Response(wsdl_file.read(), mimetype="text/xml")


@app.post("/soap")
def soap_endpoint():
    response_xml, status = service.handle(request.data)
    return Response(response_xml, status=status, mimetype="text/xml")


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
