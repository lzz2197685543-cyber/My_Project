import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ecommerce_automation.ai import AIClient, AsyncAIClient, ask_ai
from ecommerce_automation.notify import send_dingtalk_markdown
from ecommerce_automation.tasks import run_tasks, run_tasks_async

try:
    import httpx
except ImportError:
    httpx = None


class AIUtilityTests(unittest.TestCase):
    def test_one_shot_helper_closes_over_client_lifecycle(self):
        with patch("ecommerce_automation.ai.AIClient") as client_type:
            client = client_type.return_value.__enter__.return_value
            client.simple_chat.return_value = "title"
            self.assertEqual(ask_ai("prompt", api_key="key", model="model"), "title")
            client_type.assert_called_once_with("key", model="model", base_url=None)
            client.simple_chat.assert_called_once_with("prompt", system_prompt=None)

    def test_sync_chat_uses_passed_messages_and_options(self):
        class Completions:
            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="标题结果"))])

        completions = Completions()
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions), close=lambda: None)
        ai = AIClient("test-key", model="test-model", client=client)
        result = ai.simple_chat("改写标题", system_prompt="只输出标题", temperature=0.2)
        self.assertEqual(result, "标题结果")
        self.assertEqual(completions.kwargs["model"], "test-model")
        self.assertEqual(completions.kwargs["messages"][0]["content"], "只输出标题")

    def test_async_chat(self):
        class Completions:
            async def create(self, **kwargs):
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])

        class Client:
            chat = SimpleNamespace(completions=Completions())

            async def close(self):
                pass

        async def exercise():
            async with AsyncAIClient("test-key", model="test-model", client=Client()) as ai:
                self.assertEqual(await ai.simple_chat("hello"), "ok")

        asyncio.run(exercise())


class SimpleTaskUtilityTests(unittest.TestCase):
    def test_handlers_receive_dicts_and_completed_items_are_not_repeated(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "tasks.sqlite3"
            calls = []

            def handle(item):
                calls.append(item["sku"])
                return {"prepared": item["sku"]}

            rows = [{"sku": "sku-1"}, {"sku": "sku-2"}]
            first = run_tasks(rows, handle, db_path=db_path, key="sku", retry_delay=0)
            second = run_tasks(rows, handle, db_path=db_path, key="sku", retry_delay=0)

        self.assertEqual(first["succeeded"], 2)
        self.assertEqual(second["claimed"], 0)
        self.assertEqual(calls, ["sku-1", "sku-2"])

    def test_async_handler_receives_dict(self):
        with tempfile.TemporaryDirectory() as directory:
            async def handle(item):
                return {"value": item["sku"]}

            summary = asyncio.run(run_tasks_async(
                [{"sku": "sku-1"}], handle,
                db_path=Path(directory) / "tasks.sqlite3", key="sku", retry_delay=0,
            ))
        self.assertEqual(summary["succeeded"], 1)


@unittest.skipIf(httpx is None, "http extra not installed")
class DingTalkUtilityTests(unittest.TestCase):
    def test_one_shot_robot_function_delegates_message(self):
        with patch("ecommerce_automation.notify.DingTalkNotifier") as notifier_type:
            notifier = notifier_type.return_value.__enter__.return_value
            send_dingtalk_markdown("token", "secret", "title", "body")
            notifier.send_markdown.assert_called_once_with("title", "body", at_mobiles=None, is_at_all=False)

    def test_table_records_are_sent_as_bounded_batches(self):
        from ecommerce_automation.dingtalk import DingTalkTableClient

        requests = []

        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={"records": []})

        with DingTalkTableClient(
            "base", "sheet", "operator", "token",
            client=httpx.Client(transport=httpx.MockTransport(respond)),
        ) as table:
            results = table.upload_records([{"SKU": "1"}, {"SKU": "2"}, {"SKU": "3"}], batch_size=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(len(requests), 2)
        body = json.loads(requests[0].content)
        self.assertEqual(len(body["records"]), 2)
        self.assertEqual(requests[0].headers["x-acs-dingtalk-access-token"], "token")

    def test_table_operations_list_query_and_delete(self):
        from ecommerce_automation.dingtalk import DingTalkTableClient

        seen = []

        def respond(request):
            seen.append(request)
            if request.url.path.endswith("/sheets"):
                return httpx.Response(200, json={"value": [{"id": "sheet-1", "name": "库存"}]})
            if request.url.path.endswith("/records"):
                return httpx.Response(200, json={"records": [{"id": "rec-1"}], "nextToken": "next"})
            if request.url.path.endswith("/records/delete"):
                return httpx.Response(200, json={"success": True, "deletedRecordIds": ["rec-1"]})
            return httpx.Response(200, json={"success": True})

        with DingTalkTableClient(
            "base", None, "operator", "token",
            client=httpx.Client(transport=httpx.MockTransport(respond)),
        ) as document:
            self.assertEqual(document.list_sheets()[0]["name"], "库存")
            document.delete_sheet("sheet-1")
        with DingTalkTableClient(
            "base", "sheet-1", "operator", "token",
            client=httpx.Client(transport=httpx.MockTransport(respond)),
        ) as table:
            result = table.query_records(max_results=25, field_names=["SKU"])
            deleted = table.delete_records(["rec-1"])

        self.assertEqual(result["nextToken"], "next")
        self.assertEqual(deleted[0]["deletedRecordIds"], ["rec-1"])
        self.assertEqual(seen[0].url.path, "/v1.0/notable/bases/base/sheets")
        self.assertEqual(seen[1].method, "DELETE")
        self.assertEqual(seen[2].method, "GET")
        self.assertEqual(seen[2].url.params["maxResults"], "25")
        self.assertEqual(json.loads(seen[2].url.params["fieldNames"]), ["SKU"])
        self.assertEqual(json.loads(seen[3].content), {"recordIds": ["rec-1"]})

    def test_delete_rejects_http_200_with_business_failure(self):
        from ecommerce_automation.dingtalk import DingTalkTableClient

        def respond(request):
            return httpx.Response(200, json={"success": False, "message": "no write permission"})

        with DingTalkTableClient(
            "base", "sheet", "operator", "token",
            client=httpx.Client(transport=httpx.MockTransport(respond)),
        ) as table:
            with self.assertRaisesRegex(RuntimeError, "no write permission"):
                table.delete_records(["real-record-id"])
        with DingTalkTableClient(
            "base", None, "operator", "token",
            client=httpx.Client(transport=httpx.MockTransport(respond)),
        ) as table:
            with self.assertRaisesRegex(RuntimeError, "no write permission"):
                table.delete_sheet("real-sheet-id")

    def test_upload_reports_batch_details_and_error_context(self):
        from ecommerce_automation.dingtalk import DingTalkTableClient

        messages = []
        calls = []

        def respond(request):
            calls.append(request)
            if len(calls) == 1:
                return httpx.Response(200, json={"records": [{"id": "r1"}]})
            return httpx.Response(403, json={"code": "Forbidden", "message": "no permission"})

        with DingTalkTableClient(
            "base", "sheet", "operator", "token", progress=messages.append,
            client=httpx.Client(transport=httpx.MockTransport(respond)),
        ) as table:
            with self.assertRaisesRegex(RuntimeError, "第 2/2 批"):
                table.upload_records([{"SKU": "1"}, {"SKU": "2"}], batch_size=1)
        self.assertIn("第 1/2 批", messages[0])
        self.assertIn("第 2/2 批", messages[1])

    def test_work_notifier_and_user_lookups(self):
        from ecommerce_automation.dingtalk_work import DingTalkWorkNotifier

        requests = []

        def respond(request):
            requests.append(request)
            path = request.url.path
            if path.endswith("asyncsend_v2"):
                return httpx.Response(200, json={"errcode": 0, "task_id": 7})
            if path.endswith("getbymobile"):
                return httpx.Response(200, json={"errcode": 0, "result": {"userid": "user-1"}})
            return httpx.Response(200, json={"errcode": 0, "result": {"unionid": "union-1"}})

        with patch("ecommerce_automation.dingtalk_work.DingTalkTokenProvider") as token_type:
            token_type.return_value.get_access_token.return_value = "token"
            with DingTalkWorkNotifier(
                "client", "secret", "12345",
                client=httpx.Client(transport=httpx.MockTransport(respond)),
            ) as notifier:
                result = notifier.send_text("user-1", "标题", "正文")
                self.assertEqual(notifier.get_user_id_by_mobile("13800000000"), "user-1")
                self.assertEqual(notifier.get_union_id_by_user_id("user-1"), "union-1")
                self.assertEqual(notifier.get_operator_id_by_mobile("13800000000"), "union-1")

        self.assertEqual(result["task_id"], 7)
        sent = json.loads(requests[0].content)
        self.assertEqual(sent["agent_id"], 12345)
        self.assertEqual(sent["userid_list"], "user-1")
        self.assertEqual(len(requests), 5)

    def test_token_provider_caches_successful_token(self):
        from ecommerce_automation.dingtalk import DingTalkTokenProvider

        calls = []

        def respond(request):
            calls.append(request)
            return httpx.Response(200, json={"errcode": 0, "access_token": "token-1", "expires_in": 7200})

        with DingTalkTokenProvider(
            "client-id", "client-secret",
            client=httpx.Client(transport=httpx.MockTransport(respond)),
        ) as provider:
            self.assertEqual(provider.get_access_token(), "token-1")
            self.assertEqual(provider.get_access_token(), "token-1")
            self.assertEqual(provider.get_access_token(force_refresh=True), "token-1")
        self.assertEqual(len(calls), 2)

    def test_table_refreshes_token_only_after_unauthorized_response(self):
        from ecommerce_automation.dingtalk import DingTalkTableClient, DingTalkTokenProvider

        token_calls = []
        access_tokens = iter(["old-token", "new-token"])

        def token_response(request):
            token = next(access_tokens)
            token_calls.append(token)
            return httpx.Response(200, json={"errcode": 0, "access_token": token, "expires_in": 7200})

        upload_requests = []

        def upload_response(request):
            upload_requests.append(request)
            if len(upload_requests) == 1:
                return httpx.Response(401, json={"code": "InvalidToken"})
            return httpx.Response(200, json={"records": []})

        with DingTalkTokenProvider(
            "client-id", "client-secret",
            client=httpx.Client(transport=httpx.MockTransport(token_response)),
        ) as provider:
            with DingTalkTableClient(
                "base", "sheet", "operator", provider,
                client=httpx.Client(transport=httpx.MockTransport(upload_response)),
            ) as table:
                table.upload_records([{"SKU": "1"}])

        self.assertEqual(token_calls, ["old-token", "new-token"])
        self.assertEqual([request.headers["x-acs-dingtalk-access-token"] for request in upload_requests], ["old-token", "new-token"])

    def test_one_shot_upload_function_manages_clients(self):
        from ecommerce_automation.dingtalk import upload_dingtalk_records

        with patch("ecommerce_automation.dingtalk.DingTalkTokenProvider") as token_type:
            with patch("ecommerce_automation.dingtalk.DingTalkTableClient") as table_type:
                token = token_type.return_value.__enter__.return_value
                table = table_type.return_value.__enter__.return_value
                table.upload_records.return_value = [{"ok": True}]
                result = upload_dingtalk_records(
                    [{"SKU": "1"}], client_id="client", client_secret="secret",
                    base_id="base", sheet_id="sheet", operator_id="operator",
                )
        self.assertEqual(result, [{"ok": True}])
        token_type.assert_called_once_with("client", "secret")
        table_type.assert_called_once_with("base", "sheet", "operator", token, progress=print)


if __name__ == "__main__":
    unittest.main()
