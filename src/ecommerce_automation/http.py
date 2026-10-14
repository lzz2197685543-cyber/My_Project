from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable

from ._optional import require
from .errors import AuthenticationError, OutcomeUnknown, PermanentError, RetryableError

"""
它封装了 httpx，用来安全地调用 JSON API，重点解决四类问题：

失败重试：对 429/5xx 和网络错误按策略重试。

认证过期刷新：401 时刷新 token 并重放一次。

重复提交保护：非幂等方法（POST/PATCH/DELETE）默认不重放，避免重复扣款/下单等。

结果不确定处理：当无法确认请求是否已生效时，抛 OutcomeUnknown 让上层去对账，而不是盲目重试。
"""


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 1
    max_delay: float = 30
    min_interval: float = 0.2

    def __post_init__(self):
        if self.max_attempts < 1 or min(self.base_delay, self.max_delay, self.min_interval) < 0:
            raise ValueError("Invalid retry policy")

    def delay(self, attempt: int, response=None) -> float:
        if response is not None and response.headers.get("Retry-After"):
            raw = response.headers["Retry-After"]
            try:
                seconds = float(raw)
            except ValueError:
                try:
                    target = parsedate_to_datetime(raw)
                    if target.tzinfo is None:
                        target = target.replace(tzinfo=timezone.utc)
                    seconds = (target - datetime.now(timezone.utc)).total_seconds()
                except (TypeError, ValueError, OverflowError):
                    seconds = self.base_delay * 2 ** (attempt - 1)
            if seconds > self.max_delay:
                raise RetryableError("Retry-After exceeds inline retry budget; defer the task")
            return max(0, seconds)
        return min(self.max_delay, self.base_delay * 2 ** (attempt - 1))


class _ClientBase:
    def _setup(self, policy, auth_headers, is_auth_invalid, refresh_auth):
        self.policy = policy or RetryPolicy()
        self.auth_headers = auth_headers
        self.is_auth_invalid = is_auth_invalid
        self.refresh_auth = refresh_auth
        self._last_started = 0.0

    def _headers(self, headers, auth):
        merged = self.httpx.Headers(headers or {})
        merged.update(auth or {})
        return merged

    def _evaluate(self, response, *, replay_safe: bool, refreshed: bool):
        try:
            payload = response.json()
        except ValueError:
            payload = None
        auth_invalid = response.status_code == 401 or (
            self.is_auth_invalid is not None and self.is_auth_invalid(response, payload)
        )
        if auth_invalid:
            if not replay_safe or refreshed or self.refresh_auth is None:
                raise AuthenticationError("Authentication rejected; request was not replayed")
            return "refresh", None
        if response.status_code in {429, 500, 502, 503, 504}:
            if not replay_safe:
                raise OutcomeUnknown(f"HTTP {response.status_code}; reconcile the operation before replay")
            return "retry", None
        if not 200 <= response.status_code < 300:
            raise PermanentError(f"Unexpected HTTP status {response.status_code}")
        if payload is None:
            if not replay_safe:
                raise OutcomeUnknown("No usable JSON result; reconcile the operation before replay")
            raise PermanentError("Response must contain a non-null JSON result")
        return "done", payload


class HttpClient(_ClientBase):
    """JSON transport; POST/PATCH/DELETE are never replayed unless explicitly marked safe."""

    def __init__(
        self, base_url: str, *, timeout: float = 30, policy: RetryPolicy | None = None,
        auth_headers: Callable | None = None, is_auth_invalid: Callable | None = None,
        refresh_auth: Callable | None = None, transport: Any = None,
    ):
        self.httpx = require("httpx", "http")
        self._setup(policy, auth_headers, is_auth_invalid, refresh_auth)
        self._lock = threading.Lock()
        self._client = self.httpx.Client(
            base_url=base_url, timeout=timeout, follow_redirects=False, transport=transport,
        )

    def request_json(
        self, method: str, path: str, *, params=None, json=None, headers=None,
        replay_safe: bool | None = None, idempotency_key: str | None = None,
    ):
        method = method.upper()
        safe = method in {"GET", "HEAD", "OPTIONS"} if replay_safe is None else replay_safe
        refreshed = False
        with self._lock:
            for attempt in range(1, self.policy.max_attempts + 1):
                auth = self.auth_headers() if self.auth_headers else None
                time.sleep(max(0, self.policy.min_interval - (time.monotonic() - self._last_started)))
                self._last_started = time.monotonic()
                request_headers = self._headers(headers, auth)
                if idempotency_key is not None:
                    if not idempotency_key.strip() or len(idempotency_key) > 200:
                        raise ValueError("idempotency_key must contain 1-200 characters")
                    request_headers["Idempotency-Key"] = idempotency_key
                try:
                    response = self._client.request(method, path, params=params, json=json, headers=request_headers)
                except self.httpx.TransportError:
                    if not safe:
                        raise OutcomeUnknown("Transport failed; operation may already be committed") from None
                    if attempt == self.policy.max_attempts:
                        raise RetryableError("Transport failed after bounded retries") from None
                    time.sleep(self.policy.delay(attempt))
                    continue
                action, payload = self._evaluate(response, replay_safe=safe, refreshed=refreshed)
                if action == "done":
                    return payload
                if action == "refresh":
                    if attempt == self.policy.max_attempts:
                        raise AuthenticationError("No authentication replay attempts left")
                    try:
                        refreshed_ok = self.refresh_auth()
                    except Exception:
                        raise AuthenticationError("Authentication refresh failed") from None
                    if refreshed_ok is not True:
                        raise AuthenticationError("Authentication refresh did not report success")
                    refreshed = True
                elif attempt == self.policy.max_attempts:
                    raise RetryableError(f"HTTP {response.status_code} after bounded retries")
                else:
                    time.sleep(self.policy.delay(attempt, response))

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncHttpClient(_ClientBase):
    """Async equivalent; auth_headers and refresh_auth callbacks must be async."""

    def __init__(
        self, base_url: str, *, timeout: float = 30, policy: RetryPolicy | None = None,
        auth_headers: Callable | None = None, is_auth_invalid: Callable | None = None,
        refresh_auth: Callable | None = None, transport: Any = None,
    ):
        self.httpx = require("httpx", "http")
        self._setup(policy, auth_headers, is_auth_invalid, refresh_auth)
        self._lock = asyncio.Lock()
        self._client = self.httpx.AsyncClient(
            base_url=base_url, timeout=timeout, follow_redirects=False, transport=transport,
        )

    async def request_json(
        self, method: str, path: str, *, params=None, json=None, headers=None,
        replay_safe: bool | None = None, idempotency_key: str | None = None,
    ):
        method = method.upper()
        safe = method in {"GET", "HEAD", "OPTIONS"} if replay_safe is None else replay_safe
        refreshed = False
        async with self._lock:
            for attempt in range(1, self.policy.max_attempts + 1):
                auth = await self.auth_headers() if self.auth_headers else None
                await asyncio.sleep(max(0, self.policy.min_interval - (time.monotonic() - self._last_started)))
                self._last_started = time.monotonic()
                request_headers = self._headers(headers, auth)
                if idempotency_key is not None:
                    if not idempotency_key.strip() or len(idempotency_key) > 200:
                        raise ValueError("idempotency_key must contain 1-200 characters")
                    request_headers["Idempotency-Key"] = idempotency_key
                try:
                    response = await self._client.request(method, path, params=params, json=json, headers=request_headers)
                except self.httpx.TransportError:
                    if not safe:
                        raise OutcomeUnknown("Transport failed; operation may already be committed") from None
                    if attempt == self.policy.max_attempts:
                        raise RetryableError("Transport failed after bounded retries") from None
                    await asyncio.sleep(self.policy.delay(attempt))
                    continue
                action, payload = self._evaluate(response, replay_safe=safe, refreshed=refreshed)
                if action == "done":
                    return payload
                if action == "refresh":
                    if attempt == self.policy.max_attempts:
                        raise AuthenticationError("No authentication replay attempts left")
                    try:
                        refreshed_ok = await self.refresh_auth()
                    except Exception:
                        raise AuthenticationError("Authentication refresh failed") from None
                    if refreshed_ok is not True:
                        raise AuthenticationError("Authentication refresh did not report success")
                    refreshed = True
                elif attempt == self.policy.max_attempts:
                    raise RetryableError(f"HTTP {response.status_code} after bounded retries")
                else:
                    await asyncio.sleep(self.policy.delay(attempt, response))

    async def aclose(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()

