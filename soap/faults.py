from xml.etree import ElementTree as ET

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"


def soap_fault(code: str, message: str, detail: str | None = None) -> bytes:
    envelope = ET.Element(f"{{{SOAP_NS}}}Envelope")
    body = ET.SubElement(envelope, f"{{{SOAP_NS}}}Body")
    fault = ET.SubElement(body, f"{{{SOAP_NS}}}Fault")
    ET.SubElement(fault, "faultcode").text = code
    ET.SubElement(fault, "faultstring").text = message
    if detail:
        ET.SubElement(fault, "detail").text = detail
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


class SoapError(Exception):
    def __init__(self, message: str, code: str = "soap:Client", status: int = 400, detail: str | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.detail = detail
