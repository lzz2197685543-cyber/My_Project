from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import uuid4

from ..errors import LeaseLostError
from ..status import TaskStatus


@dataclass(frozen=True)
class Task:
    id: int
    queue: str
    key: str
    payload: dict[str, Any]
    status: TaskStatus
    attempts: int
    max_attempts: int
    lease_token: str | None
    result: Any
    error: str | None
    business_state: str | None
    operation_id: str | None
    remote_id: str | None


class TaskStore(Protocol):
    def claim(self, queue: str, worker_id: str, *, lease_seconds: float = 300) -> Task | None: ...
    def finish(self, task: Task, status: TaskStatus, **kwargs) -> TaskStatus: ...
    def heartbeat(self, task: Task, *, lease_seconds: float = 300) -> None: ...


def _task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"], queue=row["queue"], key=row["task_key"],
        payload=json.loads(row["payload"]), status=TaskStatus(row["status"]),
        attempts=row["attempts"], max_attempts=row["max_attempts"],
        lease_token=row["lease_token"], result=json.loads(row["result"]) if row["result"] else None,
        error=row["error"], business_state=row["business_state"],
        operation_id=row["operation_id"], remote_id=row["remote_id"],
    )


class SQLiteTaskStore:
    """Durable local queue with atomic claims and lease-token fencing."""

    def __init__(self, path: str | Path, *, clock: Callable[[], float] = time.time):
        self.path = Path(path).resolve()
        self.clock = clock

    @contextmanager
    def _write_transaction(self):
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def _read_connection(self):
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._write_transaction() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue TEXT NOT NULL, task_key TEXT NOT NULL, payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL, available_at REAL NOT NULL,
                    worker_id TEXT, lease_token TEXT, lease_until REAL,
                    result TEXT, error TEXT, business_state TEXT, operation_id TEXT, remote_id TEXT,
                    created_at REAL NOT NULL, updated_at REAL NOT NULL,
                    UNIQUE(queue, task_key)
                )
            """)
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(tasks)")}
            for name in ("business_state", "operation_id", "remote_id"):
                if name not in columns:
                    connection.execute(f"ALTER TABLE tasks ADD COLUMN {name} TEXT")
            connection.execute("CREATE INDEX IF NOT EXISTS tasks_ready ON tasks(queue, status, available_at, id)")

    def enqueue(
        self, queue: str, key: str, payload: dict, *, max_attempts: int = 3,
        business_state: str | None = None, operation_id: str | None = None,
        remote_id: str | None = None,
    ) -> bool:
        if not queue.strip() or not key.strip() or max_attempts < 1:
            raise ValueError("queue/key must be nonempty and max_attempts >= 1")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a JSON object")
        encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        now = self.clock()
        with self._write_transaction() as connection:
            cursor = connection.execute("""
                INSERT INTO tasks(queue, task_key, payload, max_attempts, available_at,
                    business_state, operation_id, remote_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(queue, task_key) DO NOTHING
            """, (queue, key, encoded, max_attempts, now, business_state,
                   operation_id, remote_id, now, now))
            return cursor.rowcount == 1

    def claim(self, queue: str, worker_id: str, *, lease_seconds: float = 300) -> Task | None:
        if lease_seconds <= 0 or not worker_id.strip():
            raise ValueError("lease_seconds must be positive and worker_id nonempty")
        now = self.clock()
        with self._write_transaction() as connection:
            connection.execute("""
                UPDATE tasks SET status='need_manual', error='lease_expired: reconcile before retry',
                    lease_token=NULL, lease_until=NULL, updated_at=?
                WHERE queue=? AND status='processing' AND lease_until<=?
            """, (now, queue, now))
            row = connection.execute("""
                SELECT * FROM tasks WHERE queue=? AND status='pending'
                    AND available_at<=? AND attempts<max_attempts ORDER BY id LIMIT 1
            """, (queue, now)).fetchone()
            if row is None:
                return None
            connection.execute("""
                UPDATE tasks SET status='processing', attempts=attempts+1, worker_id=?,
                    lease_token=?, lease_until=?, updated_at=? WHERE id=?
            """, (worker_id, uuid4().hex, now + lease_seconds, now, row["id"]))
            return _task(connection.execute("SELECT * FROM tasks WHERE id=?", (row["id"],)).fetchone())

    def heartbeat(self, task: Task, *, lease_seconds: float = 300) -> None:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        now = self.clock()
        with self._write_transaction() as connection:
            changed = connection.execute("""
                UPDATE tasks SET lease_until=?, updated_at=?
                WHERE id=? AND status='processing' AND lease_token=? AND lease_until>?
            """, (now + lease_seconds, now, task.id, task.lease_token, now)).rowcount
            if changed != 1:
                raise LeaseLostError(f"Task {task.id} no longer belongs to this worker")

    def finish(
        self, task: Task, status: TaskStatus, *, result: Any = None,
        error: str | None = None, retry_delay: float = 0,
        business_state: str | None = None, operation_id: str | None = None,
        remote_id: str | None = None,
    ) -> TaskStatus:
        status = TaskStatus(status)
        if status == TaskStatus.PROCESSING or retry_delay < 0:
            raise ValueError("Invalid completion status or retry delay")
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False)
        now = self.clock()
        with self._write_transaction() as connection:
            current = connection.execute("""
                SELECT * FROM tasks WHERE id=? AND status='processing'
                    AND lease_token=? AND lease_until>?
            """, (task.id, task.lease_token, now)).fetchone()
            if current is None:
                raise LeaseLostError(f"Task {task.id} no longer belongs to this worker")
            if status == TaskStatus.PENDING and current["attempts"] >= current["max_attempts"]:
                status = TaskStatus.FAILED
            connection.execute("""
                UPDATE tasks SET status=?, result=?, error=?, available_at=?,
                    business_state=?, operation_id=COALESCE(?, operation_id),
                    remote_id=COALESCE(?, remote_id), lease_token=NULL, lease_until=NULL,
                    updated_at=? WHERE id=?
            """, (status.value, encoded, error, now + retry_delay, business_state,
                   operation_id, remote_id, now, task.id))
        return status

    def get(self, queue: str, key: str) -> Task | None:
        with self._read_connection() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE queue=? AND task_key=?", (queue, key)).fetchone()
            return _task(row) if row else None

    def counts(self, queue: str) -> dict[str, int]:
        result = {status.value: 0 for status in TaskStatus}
        with self._read_connection() as connection:
            for row in connection.execute("SELECT status, COUNT(*) AS count FROM tasks WHERE queue=? GROUP BY status", (queue,)):
                result[row["status"]] = row["count"]
        return result

    def requeue(self, task_id: int, *, reset_attempts: bool = False) -> None:
        """Operator action after inspecting/reconciling a failed or uncertain task."""
        now = self.clock()
        with self._write_transaction() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row is None or row["status"] not in {"failed", "need_manual"}:
                raise ValueError("Only failed/need_manual tasks can be requeued")
            attempts = 0 if reset_attempts else row["attempts"]
            if attempts >= row["max_attempts"]:
                raise ValueError("Attempts exhausted; explicitly reset_attempts to retry")
            connection.execute("""
                UPDATE tasks SET status='pending', attempts=?, available_at=?,
                    lease_token=NULL, lease_until=NULL, result=NULL, error=NULL,
                    operation_id=NULL, remote_id=NULL, updated_at=? WHERE id=?
            """, (attempts, now, now, task_id))

    def resolve_manual(
        self, task_id: int, status: TaskStatus, *, result: Any = None,
        error: str | None = None, business_state: str | None = None,
        operation_id: str | None = None, remote_id: str | None = None,
    ) -> TaskStatus:
        """Record an operator's remote reconciliation decision."""
        status = TaskStatus(status)
        if status not in {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.SKIPPED}:
            raise ValueError("Manual resolution must be succeeded, failed or skipped")
        now = self.clock()
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False)
        with self._write_transaction() as connection:
            changed = connection.execute("""
                UPDATE tasks SET status=?, result=?, error=?, business_state=?,
                    operation_id=COALESCE(?, operation_id), remote_id=COALESCE(?, remote_id),
                    lease_token=NULL, lease_until=NULL, updated_at=?
                WHERE id=? AND status='need_manual'
            """, (status.value, encoded, error, business_state, operation_id,
                   remote_id, now, task_id)).rowcount
            if changed != 1:
                raise ValueError("Only need_manual tasks can be resolved")
        return status
