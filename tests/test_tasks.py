import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from ecommerce_automation import TaskOutcome
from ecommerce_automation.errors import (
    AuthenticationError, LeaseLostError, OutcomeUnknown, PermanentError, RetryableError, SkipTask,
)
from ecommerce_automation.tasks import AsyncTaskRunner, SQLiteTaskStore, TaskRunner, TaskStatus


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.now = 1000.0
        self.path = Path(self.directory.name) / "tasks.sqlite3"
        self.store = SQLiteTaskStore(self.path, clock=lambda: self.now)
        self.store.initialize()

    def test_dedup_is_persistent_and_scoped_by_queue(self):
        self.assertTrue(self.store.enqueue("collect", "sku1", {"version": 1}))
        self.assertFalse(self.store.enqueue("collect", "sku1", {"version": 2}))
        self.assertTrue(self.store.enqueue("publish", "sku1", {}))
        reopened = SQLiteTaskStore(self.path)
        self.assertEqual(reopened.get("collect", "sku1").payload, {"version": 1})

    def test_business_fields_are_separate_from_execution_status(self):
        self.store.enqueue("finance", "temu:2026-10:shop1", {"month": "2026-10"},
                           business_state="downloaded", operation_id="download-1")
        task = self.store.claim("finance", "worker")
        self.store.finish(task, TaskOutcome.success(
            {"matched": 1280}, business_state="reconciled", operation_id="match-1", remote_id="report-1",
        ).status, result={"matched": 1280}, business_state="reconciled",
                         operation_id="match-1", remote_id="report-1")
        saved = self.store.get("finance", "temu:2026-10:shop1")
        self.assertEqual(saved.status.value, "succeeded")
        self.assertEqual(saved.business_state, "reconciled")
        self.assertEqual(saved.operation_id, "match-1")
        self.assertEqual(saved.remote_id, "report-1")

    def test_concurrent_workers_never_claim_same_row(self):
        for number in range(30):
            self.store.enqueue("queue", str(number), {})
        with ThreadPoolExecutor(max_workers=8) as executor:
            claimed = list(executor.map(lambda worker: self.store.claim("queue", str(worker)), range(40)))
        identifiers = [task.id for task in claimed if task]
        self.assertEqual(len(identifiers), 30)
        self.assertEqual(len(set(identifiers)), 30)

    def test_expired_task_is_manual_and_stale_worker_is_fenced(self):
        self.store.enqueue("queue", "sku", {})
        first = self.store.claim("queue", "worker1", lease_seconds=10)
        self.now += 11
        self.assertIsNone(self.store.claim("queue", "worker2"))
        self.assertEqual(self.store.get("queue", "sku").status, TaskStatus.NEED_MANUAL)
        with self.assertRaises(LeaseLostError):
            self.store.finish(first, TaskStatus.SUCCEEDED)
        self.store.requeue(first.id)
        second = self.store.claim("queue", "worker2")
        self.assertNotEqual(first.lease_token, second.lease_token)
        with self.assertRaises(LeaseLostError):
            self.store.finish(first, TaskStatus.FAILED)
        self.store.finish(second, TaskStatus.SUCCEEDED, result={"remote_id": "123"})
        self.assertEqual(self.store.get("queue", "sku").result, {"remote_id": "123"})

    def test_heartbeat_extends_lease_and_finished_task_cannot_be_overwritten(self):
        self.store.enqueue("queue", "sku", {})
        task = self.store.claim("queue", "worker", lease_seconds=10)
        self.now += 9
        self.store.heartbeat(task, lease_seconds=10)
        self.now += 5
        self.store.finish(task, TaskStatus.SUCCEEDED)
        with self.assertRaises(LeaseLostError):
            self.store.finish(task, TaskStatus.FAILED)

    def test_retry_delay_and_attempt_limit(self):
        self.store.enqueue("queue", "sku", {}, max_attempts=2)
        task = self.store.claim("queue", "worker")
        status = self.store.finish(task, TaskStatus.PENDING, retry_delay=30)
        self.assertEqual(status, TaskStatus.PENDING)
        self.assertIsNone(self.store.claim("queue", "worker"))
        self.now += 30
        second = self.store.claim("queue", "worker")
        self.assertEqual(second.attempts, 2)
        status = self.store.finish(second, TaskStatus.PENDING)
        self.assertEqual(status, TaskStatus.FAILED)
        with self.assertRaises(ValueError):
            self.store.requeue(second.id)

    def test_runner_classifies_failures_and_does_not_repeat_success(self):
        failures = {"retry": RetryableError, "bad": PermanentError, "unknown": OutcomeUnknown, "skip": SkipTask}
        for key in ["ok", *failures]:
            self.store.enqueue("queue", key, {}, max_attempts=1)
        def handle(task):
            if task.key in failures:
                raise failures[task.key]("expected")
            return {"done": True}
        result = TaskRunner(self.store, retry_delay=0).run("queue", handle)
        self.assertEqual(result.claimed, 5)
        self.assertEqual(result.outcomes["succeeded"], 1)
        self.assertEqual(result.outcomes["failed"], 2)
        self.assertEqual(result.outcomes["need_manual"], 1)
        self.assertEqual(result.outcomes["skipped"], 1)
        self.assertEqual(TaskRunner(self.store).run("queue", handle).claimed, 0)

    def test_auth_failure_stops_batch_without_consuming_other_tasks(self):
        for key in ["first", "second"]:
            self.store.enqueue("queue", key, {})
        def handle(task):
            raise AuthenticationError("login required")
        result = TaskRunner(self.store).run("queue", handle)
        self.assertEqual(result.claimed, 1)
        self.assertEqual(self.store.get("queue", "second").attempts, 0)

    def test_sync_runner_does_not_mark_coroutine_successful(self):
        self.store.enqueue("queue", "sku", {})
        async def async_handler(task):
            return {"done": True}
        with self.assertRaises(ValueError):
            TaskRunner(self.store).run("queue", async_handler)
        self.assertEqual(self.store.get("queue", "sku").attempts, 0)

    def test_async_runner_persists_result(self):
        self.store.enqueue("queue", "sku", {})
        async def handler(task):
            return {"confirmed": task.key}
        summary = asyncio.run(AsyncTaskRunner(self.store).run("queue", handler))
        self.assertEqual(summary.outcomes["succeeded"], 1)
        self.assertEqual(self.store.get("queue", "sku").result, {"confirmed": "sku"})

    def test_runner_accepts_explicit_outcome(self):
        self.store.enqueue("queue", "sku", {})
        def handler(task):
            return TaskOutcome.success({"rows": 3}, business_state="exported", remote_id="file-1")
        TaskRunner(self.store).run("queue", handler)
        task = self.store.get("queue", "sku")
        self.assertEqual(task.business_state, "exported")
        self.assertEqual(task.remote_id, "file-1")


if __name__ == "__main__":
    unittest.main()
