from __future__ import annotations

STATE = {
    "users": [],
    "roles": {
        1: "admin",
        2: "manager",
        3: "customer",
    },
    "authors": [
        {"id": 1, "name": "Gabriel García Márquez", "country": "Colombia"},
        {"id": 2, "name": "Haruki Murakami", "country": "Japón"},
    ],
    "orders": {},
    "payments": [],
}


def reset_state():
    STATE["users"] = []
    STATE["authors"] = [
        {"id": 1, "name": "Gabriel García Márquez", "country": "Colombia"},
        {"id": 2, "name": "Haruki Murakami", "country": "Japón"},
    ]
    STATE["orders"] = {}
    STATE["payments"] = []
