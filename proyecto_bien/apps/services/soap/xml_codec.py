"""XML representations for catalog responses and HTTP errors."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from xml.etree import ElementTree as ET


def _text(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return "" if value is None else str(value)


def _element(parent: ET.Element, name: str, value: Any) -> None:
    node = ET.SubElement(parent, name)
    if isinstance(value, dict):
        for child_name, child_value in value.items():
            _element(node, child_name, child_value)
    elif isinstance(value, list):
        for item in value:
            _element(node, "item", item)
    else:
        node.text = _text(value)


def _document(root_name: str) -> ET.Element:
    return ET.Element(root_name)


def serialize_library(books: list[dict[str, Any]]) -> bytes:
    root = _document("library")
    for book in books:
        node = ET.SubElement(root, "book")
        for key in (
            "isbn", "title", "author", "publicationYear", "publisher", "price",
            "stock", "description", "format", "imageUrl",
        ):
            if key in book:
                _element(node, key, book[key])
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def serialize_minimal(books: list[dict[str, Any]]) -> bytes:
    root = _document("library")
    for book in books:
        node = ET.SubElement(root, "book")
        for key in ("isbn", "title", "author", "imageUrl"):
            _element(node, key, book.get(key))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def serialize_concepts(concepts: list[dict[str, Any]]) -> bytes:
    root = _document("cloudConcepts")
    for concept in concepts:
        _element(root, "concept", concept)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def serialize_message(message: str, **attributes: Any) -> bytes:
    root = _document("response")
    _element(root, "message", message)
    for key, value in attributes.items():
        _element(root, key, value)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def serialize_error(message: str, status: int) -> bytes:
    return serialize_message(message, status=status)


def serialize_payload(payload: dict[str, Any] | list[Any], root_name: str = "response") -> bytes:
    """Serialize simple HTTP payloads that are not catalog-specific."""
    root = _document(root_name)
    if isinstance(payload, dict):
        for key, value in payload.items():
            _element(root, key, value)
    else:
        _element(root, "items", payload)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
