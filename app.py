"""Flask entry point for the independent library SOAP service."""
from flask import Flask, Response, request

from config.settings import settings
from db.repository import DatabaseRepository
from soap.service import SoapService

app = Flask(__name__)
repository = DatabaseRepository(settings.db_config)
service = SoapService(repository)


@app.get("/health")
def health():
    return {"status": "ok", "service": "library-classifier-soap"}


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
