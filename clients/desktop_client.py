"""Manual SOAP client used by the desktop GUI; it never connects to PostgreSQL."""
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
NS = "urn:udem:library:classifier"


def request_envelope(operation: str, fields: dict[str, str], header: str = "") -> bytes:
    # The XSD uses elementFormDefault="qualified": operation fields must use
    # the service namespace as well as the operation itself.
    body = "".join(
        f"<tns:{key}>{escape(value)}</tns:{key}>" for key, value in fields.items()
    )
    return (f'<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="{SOAP_NS}" xmlns:tns="{NS}">'
            f"<soap:Header>{header}</soap:Header><soap:Body><tns:{operation}>{body}</tns:{operation}></soap:Body></soap:Envelope>").encode()


class SoapClientError(Exception):
    pass


class LibrarySoapClient:
    def __init__(self, endpoint: str = "http://127.0.0.1:5000/soap"):
        self.endpoint = endpoint

    def call(self, operation: str, fields: dict[str, str], header: str = "") -> ET.Element:
        request = Request(self.endpoint, data=request_envelope(operation, fields, header), method="POST")
        request.add_header("Content-Type", "text/xml; charset=utf-8")
        try:
            with urlopen(request, timeout=10) as response:
                root = ET.fromstring(response.read())
        except Exception as error:
            raise SoapClientError("No se pudo contactar el servicio SOAP.") from error
        fault = root.find(f".//{{{SOAP_NS}}}Fault")
        if fault is not None:
            raise SoapClientError(fault.findtext("faultstring") or "Error SOAP no especificado.")
        return root

    def pending(self, client_type: str, client_id: str):
        return self.call("ObtenerConceptosPendientes", {"clientType": client_type, "clientId": client_id})

    def classify(self, data: dict[str, str]):
        return self.call("RegistrarClasificacion", data)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:5000/soap")
    parser.add_argument("--client-id", default="desktop-demo")
    args = parser.parse_args()
    print(LibrarySoapClient(args.endpoint).pending("python-gui", args.client_id).tag)
