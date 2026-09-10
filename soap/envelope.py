from xml.etree import ElementTree as ET

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
SERVICE_NS = "urn:udem:library:classifier"
ET.register_namespace("soap", SOAP_NS)
ET.register_namespace("tns", SERVICE_NS)


def child_text(element: ET.Element, name: str, required: bool = True) -> str | None:
    value = element.findtext(f"{{{SERVICE_NS}}}{name}")
    value = value.strip() if value else None
    if required and not value:
        raise ValueError(f"El campo '{name}' es obligatorio.")
    return value


def parse_request(xml_bytes: bytes) -> tuple[str, ET.Element, ET.Element]:
    root = ET.fromstring(xml_bytes)
    if root.tag != f"{{{SOAP_NS}}}Envelope":
        raise ValueError("El documento no contiene un SOAP Envelope válido.")
    header = root.find(f"{{{SOAP_NS}}}Header")
    body = root.find(f"{{{SOAP_NS}}}Body")
    if body is None:
        raise ValueError("El SOAP Envelope no contiene Body.")
    operations = list(body)
    if len(operations) != 1:
        raise ValueError("El SOAP Body no contiene una operación.")
    operation = operations[0]
    if not operation.tag.startswith(f"{{{SERVICE_NS}}}"):
        raise ValueError("La operación SOAP no pertenece al namespace del servicio.")
    return operation.tag.rsplit("}", 1)[-1], header if header is not None else ET.Element("Header"), operation


def envelope(response_name: str, fields: dict, collection_name: str | None = None) -> bytes:
    root = ET.Element(f"{{{SOAP_NS}}}Envelope")
    body = ET.SubElement(root, f"{{{SOAP_NS}}}Body")
    response = ET.SubElement(body, f"{{{SERVICE_NS}}}{response_name}")
    if collection_name:
        collection = ET.SubElement(response, f"{{{SERVICE_NS}}}{collection_name}")
        for item in fields:
            node = ET.SubElement(collection, f"{{{SERVICE_NS}}}item")
            for key, value in item.items():
                ET.SubElement(node, f"{{{SERVICE_NS}}}{key}").text = str(value or "")
    else:
        for key, value in fields.items():
            ET.SubElement(response, f"{{{SERVICE_NS}}}{key}").text = str(value or "")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
