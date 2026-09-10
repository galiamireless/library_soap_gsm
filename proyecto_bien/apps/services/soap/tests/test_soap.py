from apps.services.soap.soap_service import SoapService


SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
SERVICE_NS = "urn:udem:library:classifier"


class FakeRepository:
    def list_pending_concepts(self, client_type, client_id):
        return [{"conceptId": 1, "isbn": "9786070001001", "concept": "IaaS", "title": "Libro"}]

    def register_classification(self, data):
        return {"classificationId": 1, "classifiedAt": "2026-09-10T12:00:00+00:00"}

    def get_user_progress(self, email, client_type, client_id):
        return {"email": email, "classified": 0, "pending": 1}

    def get_statistics(self, client_type, client_id):
        return [{"model": "IaaS", "count": 1}]


def envelope(operation, fields):
    values = "".join(f"<tns:{key}>{value}</tns:{key}>" for key, value in fields.items())
    return (
        f'<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:tns="{SERVICE_NS}">'
        f"<soap:Body><tns:{operation}>{values}</tns:{operation}></soap:Body></soap:Envelope>"
    ).encode()


def test_pending_operation_returns_soap_response():
    payload = envelope("ObtenerConceptosPendientes", {"clientType": "test", "clientId": "1"})

    response, status = SoapService(FakeRepository()).handle(payload)

    assert status == 200
    assert b"ObtenerConceptosPendientesResponse" in response
    assert b"IaaS" in response


def test_unqualified_fields_are_rejected_as_invalid_contract():
    payload = (
        f'<soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:tns="{SERVICE_NS}">'
        '<soap:Body><tns:ObtenerConceptosPendientes><clientType>test</clientType>'
        '<clientId>1</clientId></tns:ObtenerConceptosPendientes></soap:Body></soap:Envelope>'
    ).encode()

    response, status = SoapService(FakeRepository()).handle(payload)

    assert status == 400
    assert b"Fault" in response
