"""JSON encoding kept separate from HTTP route registration."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _default(value: Any):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Tipo no serializable: {type(value).__name__}")


def dumps(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, default=_default).encode("utf-8")
