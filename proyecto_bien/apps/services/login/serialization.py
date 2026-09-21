from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from html import escape
from typing import Any


def json_bytes(payload: Any) -> bytes:
    def default(value: Any):
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        raise TypeError(f"Tipo no serializable: {type(value).__name__}")

    return json.dumps(payload, ensure_ascii=False, default=default).encode("utf-8")


def xml_bytes(payload: Any, root: str = "response") -> bytes:
    def render(value: Any, tag: str) -> str:
        if isinstance(value, dict):
            children = "".join(render(child, str(key)) for key, child in value.items())
            return f"<{tag}>{children}</{tag}>"
        if isinstance(value, (list, tuple)):
            return "".join(render(child, "item") for child in value)
        if isinstance(value, (date, datetime)):
            value = value.isoformat()
        safe_value = escape(str(value if value is not None else ""))
        return f"<{tag}>{safe_value}</{tag}>"

    return ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + render(payload, root)).encode("utf-8")
