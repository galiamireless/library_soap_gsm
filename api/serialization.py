"""Stable JSON/XML representations for the legacy HTTP endpoints."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from xml.etree import ElementTree as ET

from flask import Response, jsonify, request


def response_format() -> str:
    value = request.args.get("format", "xml").strip().lower()
    # Keep the original endpoint behavior: unknown values fall back to XML.
    return "json" if value == "json" else "xml"


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


def _xml_value(parent: ET.Element, key: str, value) -> None:
    if isinstance(value, list):
        container = ET.SubElement(parent, key)
        for item in value:
            _xml_value(container, "item", item)
        return
    element = ET.SubElement(parent, key)
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            _xml_value(element, child_key, child_value)
    elif value is not None:
        element.text = str(value)


def serialize(data, status: int = 200):
    """Serialize a response using the requested legacy format."""
    if response_format() == "json":
        return jsonify(json_safe(data)), status

    root = ET.Element("response")
    if isinstance(data, dict):
        for key, value in data.items():
            _xml_value(root, key, value)
    else:
        _xml_value(root, "items", data)
    return Response(
        ET.tostring(root, encoding="unicode"),
        status=status,
        content_type="application/xml; charset=utf-8",
    )


def serialize_error_response(message: str, status: int):
    """Return errors in the same format as normal HTTP responses."""
    try:
        return serialize({"error": message}, status)
    except ValueError:
        root = ET.Element("response")
        _xml_value(root, "error", message)
        return Response(
            ET.tostring(root, encoding="unicode"),
            status=status,
            content_type="application/xml; charset=utf-8",
        )
