from xml.etree import ElementTree as ET

from soap.service import SoapService

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS = "urn:udem:library:classifier"


class FakeRepository:
    def list_pending_concepts(self, client_type, client_id):
        return [{"conceptId": 7, "isbn": "978-test", "concept": "Cloud", "definition": "x", "title": "Libro", "category": "Tecnología"}]

    def register_classification(self, data):
        return {"classificationId": 10, "classifiedAt": "2026-09-04T12:00:00+00:00"}

    def get_user_progress(self, email, client_type, client_id):
        return {"email": email, "classified": 1, "pending": 2}

    def get_statistics(self, client_type, client_id):
        return [{"model": "IaaS", "count": 1}]


def request(operation, fields, header=""):
    values = "".join(f"<tns:{key}>{value}</tns:{key}>" for key, value in fields.items())
    return f'<soap:Envelope xmlns:soap="{SOAP}" xmlns:tns="{NS}"><soap:Header>{header}</soap:Header><soap:Body><tns:{operation}>{values}</tns:{operation}></soap:Body></soap:Envelope>'.encode()


def test_pending_concepts():
    xml, status = SoapService(FakeRepository()).handle(request("ObtenerConceptosPendientes", {"clientType": "test", "clientId": "1"}))
    assert status == 200
    assert b"Cloud" in xml


def test_invalid_model_returns_fault():
    xml, status = SoapService(FakeRepository()).handle(request("RegistrarClasificacion", {
        "firstName": "A", "lastName": "B", "email": "a@example.com", "conceptId": "7",
        "isbn": "978-test", "model": "Invalid", "clientType": "test", "clientId": "1"}))
    assert status == 400
    assert b"Fault" in xml
    assert b"modelo Cloud" in xml


def test_invalid_xml_returns_fault():
    xml, status = SoapService(FakeRepository()).handle(b"<not-xml")
    assert status == 400
    assert b"XML inv" in xml


def test_stats_requires_security():
    xml, status = SoapService(FakeRepository()).handle(request("ObtenerEstadisticasPorModelo", {"clientType": "test", "clientId": "1"}))
    assert status == 401
    assert b"Autenticaci" in xml
