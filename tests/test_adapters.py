import asyncio
import base64
import hashlib
import hmac
import unittest
from unittest.mock import patch

from ecommerce_automation.errors import AuthenticationError, OutcomeUnknown, PermanentError, RetryableError
from ecommerce_automation.http import AsyncHttpClient, HttpClient, RetryPolicy
from ecommerce_automation.notify import DingTalkNotifier
from ecommerce_automation.storage import BaseDAO, MySQLConfig, RedisDeduplicator

try:
    import httpx
except ImportError:
    httpx = None


@unittest.skipIf(httpx is None, "http extra not installed")
class HttpTests(unittest.TestCase):
    def setUp(self):
        self.policy = RetryPolicy(max_attempts=3, base_delay=0, max_delay=0, min_interval=0)

    def test_get_retries_503_and_business_error_is_not_assumed_auth_failure(self):
        calls = []
        def respond(request):
            calls.append(request)
            if len(calls) == 1:
                return httpx.Response(503, json={})
            return httpx.Response(200, json={"code": 500, "msg": "ordinary business error"})
        with HttpClient("https://example.test", policy=self.policy, transport=httpx.MockTransport(respond)) as client:
            payload = client.request_json("GET", "/goods")
        self.assertEqual(len(calls), 2)
        self.assertEqual(payload["code"], 500)

    def test_post_timeout_is_not_replayed(self):
        calls = []
        def respond(request):
            calls.append(request)
            raise httpx.ReadTimeout("secret-url-token", request=request)
        with HttpClient("https://example.test", policy=self.policy, transport=httpx.MockTransport(respond)) as client:
            with self.assertRaises(OutcomeUnknown) as raised:
                client.request_json("POST", "/publish", json={"sku": 1})
        self.assertNotIn("secret-url-token", str(raised.exception))
        self.assertEqual(len(calls), 1)

    def test_auth_refresh_updates_headers_once(self):
        state = {"token": "old", "refreshes": 0, "calls": 0}
        def refresh():
            state.update(token="new", refreshes=state["refreshes"] + 1)
            return True
        def respond(request):
            state["calls"] += 1
            return httpx.Response(401 if request.headers["Authorization"] == "old" else 200, json={"ok": True})
        with HttpClient(
            "https://example.test", policy=self.policy,
            auth_headers=lambda: {"Authorization": state["token"]}, refresh_auth=refresh,
            transport=httpx.MockTransport(respond),
        ) as client:
            self.assertEqual(client.request_json("GET", "/goods"), {"ok": True})
        self.assertEqual(state["refreshes"], 1)
        self.assertEqual(state["calls"], 2)

    def test_repeated_auth_failure_stops(self):
        calls = []
        def respond(request):
            calls.append(request)
            return httpx.Response(401, json={})
        with HttpClient(
            "https://example.test", policy=self.policy, refresh_auth=lambda: True,
            transport=httpx.MockTransport(respond),
        ) as client:
            with self.assertRaises(AuthenticationError):
                client.request_json("GET", "/goods")
        self.assertEqual(len(calls), 2)

    def test_refresh_error_is_explicit_and_does_not_leak_credentials(self):
        def refresh():
            raise ValueError("test-secret in login response")
        with HttpClient(
            "https://example.test", policy=self.policy, refresh_auth=refresh,
            transport=httpx.MockTransport(lambda request: httpx.Response(401, json={})),
        ) as client:
            with self.assertRaises(AuthenticationError) as raised:
                client.request_json("GET", "/goods")
        self.assertNotIn("test-secret", str(raised.exception))

    def test_auth_header_override_is_case_insensitive(self):
        requests = []
        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={"ok": True})
        with HttpClient(
            "https://example.test", policy=self.policy,
            auth_headers=lambda: {"Authorization": "new"},
            transport=httpx.MockTransport(respond),
        ) as client:
            client.request_json("GET", "/goods", headers={"authorization": "stale"})
        self.assertEqual(requests[0].headers["authorization"], "new")

    def test_post_auth_failure_does_not_replay(self):
        with HttpClient(
            "https://example.test", policy=self.policy,
            refresh_auth=lambda: self.fail("Unsafe request must not be refreshed/replayed"),
            transport=httpx.MockTransport(lambda request: httpx.Response(401, json={})),
        ) as client:
            with self.assertRaises(AuthenticationError):
                client.request_json("POST", "/publish")

    def test_retry_after_budget_is_respected(self):
        calls = []
        def respond(request):
            calls.append(request)
            return httpx.Response(429, headers={"Retry-After": "120"}, json={})
        with HttpClient("https://example.test", policy=self.policy, transport=httpx.MockTransport(respond)) as client:
            with self.assertRaises(RetryableError):
                client.request_json("GET", "/goods")
        self.assertEqual(len(calls), 1)

    def test_explicit_replay_safe_post_can_retry(self):
        calls = []
        def respond(request):
            calls.append(request)
            return httpx.Response(503 if len(calls) < 2 else 200, json={"ok": True})
        with HttpClient("https://example.test", policy=self.policy, transport=httpx.MockTransport(respond)) as client:
            client.request_json("POST", "/search", replay_safe=True)
        self.assertEqual(len(calls), 2)

    def test_idempotency_key_is_forwarded(self):
        requests = []
        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={"ok": True})
        with HttpClient("https://example.test", policy=self.policy, transport=httpx.MockTransport(respond)) as client:
            client.request_json("POST", "/sync", json={"sku": "1"},
                                replay_safe=True, idempotency_key="inventory:shop1:sku1:v2")
        self.assertEqual(requests[0].headers["idempotency-key"], "inventory:shop1:sku1:v2")

    def test_async_refresh_and_transport_cleanup(self):
        async def exercise():
            state = {"token": "old"}
            async def auth():
                return {"Authorization": state["token"]}
            async def refresh():
                state["token"] = "new"
                return True
            async def respond(request):
                return httpx.Response(401 if request.headers["Authorization"] == "old" else 200, json={"ok": True})
            async with AsyncHttpClient(
                "https://example.test", policy=self.policy, auth_headers=auth,
                refresh_auth=refresh, transport=httpx.MockTransport(respond),
            ) as client:
                self.assertEqual(await client.request_json("GET", "/goods"), {"ok": True})
            self.assertTrue(client._client.is_closed)
        asyncio.run(exercise())

    def test_dingtalk_sign_and_business_success(self):
        requests = []
        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={"errcode": 0})
        with patch("ecommerce_automation.notify.time.time", return_value=1000):
            with DingTalkNotifier("test-token", "test-secret", transport=httpx.MockTransport(respond)) as notifier:
                notifier.send_text("test")
        params = requests[0].url.params
        expected = base64.b64encode(hmac.new(b"test-secret", b"1000000\ntest-secret", hashlib.sha256).digest()).decode()
        self.assertEqual(params["sign"], expected)
        self.assertEqual(params["timestamp"], "1000000")
        self.assertEqual(params["access_token"], "test-token")

    def test_dingtalk_200_with_error_is_failure(self):
        with DingTalkNotifier(
            "test-token", "test-secret", transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"errcode": 310000})),
        ) as notifier:
            with self.assertRaises(PermanentError):
                notifier.send_text("test")

    def test_dingtalk_markdown_payload_and_mentions(self):
        requests = []

        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={"errcode": 0})

        with DingTalkNotifier("test-token", "test-secret", transport=httpx.MockTransport(respond)) as notifier:
            notifier.send_markdown("title", "**body**", at_mobiles=["13800000000"])
        self.assertIn(b'"msgtype":"markdown"', requests[0].content)
        self.assertIn(b"13800000000", requests[0].content)


class FakeCursor:
    def __init__(self):
        self.closed = False
        self.operations = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def execute(self, sql, params=None):
        self.operations.append((sql, params))
        return 1


class FakeConnection:
    def __init__(self):
        self.commits = self.rollbacks = 0
        self.begins = 0
        self.closed = False
        self.current_cursor = FakeCursor()

    def cursor(self):
        if self.begins != 1:
            raise AssertionError("Explicit begin is required to disable DBUtils query replay")
        return self.current_cursor

    def begin(self):
        self.begins += 1

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class FakePool:
    def __init__(self):
        self.current_connection = FakeConnection()

    def connection(self):
        return self.current_connection


class StorageTests(unittest.TestCase):
    def test_transaction_commits_all_operations_together(self):
        pool = FakePool()
        with BaseDAO(pool).transaction() as cursor:
            cursor.execute("INSERT A", (1,))
            cursor.execute("INSERT B", (2,))
        self.assertEqual(pool.current_connection.commits, 1)
        self.assertEqual(pool.current_connection.begins, 1)
        self.assertEqual(pool.current_connection.rollbacks, 0)
        self.assertEqual(len(pool.current_connection.current_cursor.operations), 2)
        self.assertTrue(pool.current_connection.closed)

    def test_failure_rolls_back_and_releases_connection(self):
        pool = FakePool()
        with self.assertRaises(ValueError):
            with BaseDAO(pool).transaction() as cursor:
                cursor.execute("INSERT A", (1,))
                raise ValueError("failed second operation")
        self.assertEqual(pool.current_connection.commits, 0)
        self.assertEqual(pool.current_connection.rollbacks, 1)
        self.assertTrue(pool.current_connection.closed)
        self.assertTrue(pool.current_connection.current_cursor.closed)

    def test_mysql_config_does_not_reveal_password(self):
        config = MySQLConfig("localhost", "user", "test-private-password", "db")
        self.assertNotIn("test-private-password", repr(config))

    def test_redis_markers_are_scoped_and_mark_after_success(self):
        class Client:
            def __init__(self):
                self.values = {}
            def exists(self, key):
                return key in self.values
            def set(self, key, value, nx, ex):
                if key in self.values and nx:
                    return False
                self.values[key] = value
                return True
        client = Client()
        first = RedisDeduplicator(client, namespace="shop1")
        second = RedisDeduplicator(client, namespace="shop2")
        self.assertFalse(first.is_done("sku"))
        self.assertTrue(first.mark_done("sku"))
        self.assertTrue(first.is_done("sku"))
        self.assertFalse(second.is_done("sku"))
        self.assertFalse(first.mark_done("sku"))
        with self.assertRaises(ValueError):
            first.mark_done("sku", ttl_seconds=0)


if __name__ == "__main__":
    unittest.main()
