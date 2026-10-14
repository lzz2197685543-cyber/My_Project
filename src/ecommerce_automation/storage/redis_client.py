from __future__ import annotations

from hashlib import sha256

from .._optional import require
from ..logging import safe_name


class RedisDeduplicator:
    """Success markers, not a work lock. Mark only after durable business success."""

    def __init__(self, client, *, namespace: str):
        self.client = client
        self.namespace = safe_name(namespace)
        self._owns_client = False

    @classmethod
    def from_url(cls, url: str, *, namespace: str, timeout: float = 5):
        redis = require("redis", "redis")
        instance = cls(redis.Redis.from_url(
            url, decode_responses=True, socket_timeout=timeout,
            socket_connect_timeout=timeout,
        ), namespace=namespace)
        instance._owns_client = True
        return instance

    def _key(self, key: str) -> str:
        return f"ea:{self.namespace}:done:{sha256(key.encode('utf-8')).hexdigest()}"

    def is_done(self, key: str) -> bool:
        return bool(self.client.exists(self._key(key)))

    def mark_done(self, key: str, *, ttl_seconds: int | None = None) -> bool:
        if ttl_seconds is not None and ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        return bool(self.client.set(self._key(key), "1", nx=True, ex=ttl_seconds))

    def filter_new(self, keys: list[str]) -> list[str]:
        unique = list(dict.fromkeys(keys))
        if not unique:
            return []
        with self.client.pipeline(transaction=False) as pipeline:
            for key in unique:
                pipeline.exists(self._key(key))
            results = pipeline.execute()
        return [key for key, exists in zip(unique, results) if not exists]

    def close(self):
        if self._owns_client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
