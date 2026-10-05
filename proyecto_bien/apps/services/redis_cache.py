from __future__ import annotations

import json
import os
from typing import Any

try:
    import redis as redis_client
except Exception:  # pragma: no cover - optional dependency
    redis_client = None


class RedisCache:
    def __init__(self, url: str | None = None, prefix: str = "project_bien"):
        self.prefix = prefix
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        if redis_client is not None:
            try:
                self._client = redis_client.Redis.from_url(self.url, decode_responses=True)
                self._client.ping()
            except Exception:
                self._client = None

    def _key(self, name: str) -> str:
        return f"{self.prefix}:{name}"

    def get(self, name: str) -> Any | None:
        if self._client is None:
            return None
        value = self._client.get(self._key(name))
        if value is None:
            return None
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value

    def set(self, name: str, value: Any, ttl: int | None = 60) -> None:
        if self._client is None:
            return
        payload = json.dumps(value, default=str)
        if ttl is None:
            self._client.set(self._key(name), payload)
        else:
            self._client.set(self._key(name), payload, ex=ttl)

    def delete(self, name: str) -> None:
        if self._client is not None:
            self._client.delete(self._key(name))


cache = RedisCache()
