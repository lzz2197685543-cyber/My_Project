"""Function-style helpers for running ordinary dict-based business handlers."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from .runner import AsyncTaskRunner, TaskRunner
from .store import SQLiteTaskStore, Task


def _prepare_items(items, key):
    rows = list(items)
    if isinstance(key, str):
        key_for = lambda item: item.get(key)
    elif callable(key):
        key_for = key
    else:
        raise TypeError("key must be a field name or a function")
    for item in rows:
        if not isinstance(item, Mapping):
            raise TypeError("run_tasks items must be mappings such as dict")
        if not isinstance(item, dict):
            raise TypeError("run_tasks items must be dict values so they can be stored as JSON")
        task_key = key_for(item)
        if task_key is None or not str(task_key).strip():
            raise ValueError(f"Task key is missing from item: {key!r}")
    return rows, key_for


def run_tasks(
    items: Iterable[dict[str, Any]],
    handler: Callable[[dict[str, Any]], Any],
    *,
    db_path: str | Path,
    key: str | Callable[[dict[str, Any]], Any],
    queue: str = "default",
    max_attempts: int = 3,
    retry_delay: float = 30,
    limit: int = 1000,
    logger: Any = None,
) -> dict[str, int]:
    """Run dict-based handlers with SQLite deduplication and resume support.

    The handler receives the original item dictionary, never an internal ``Task``.
    Calling the function again with the same database, queue and key resumes pending
    work and skips items already completed.
    """
    rows, key_for = _prepare_items(items, key)
    store = SQLiteTaskStore(db_path)
    store.initialize()
    for item in rows:
        store.enqueue(queue, str(key_for(item)), item, max_attempts=max_attempts)

    def handle(task: Task):
        return handler(task.payload)

    return TaskRunner(store, logger=logger, retry_delay=retry_delay).run(
        queue, handle, limit=limit,
    ).as_dict()


async def run_tasks_async(
    items: Iterable[dict[str, Any]],
    handler: Callable[[dict[str, Any]], Any],
    *,
    db_path: str | Path,
    key: str | Callable[[dict[str, Any]], Any],
    queue: str = "default",
    max_attempts: int = 3,
    retry_delay: float = 30,
    limit: int = 1000,
    logger: Any = None,
) -> dict[str, int]:
    """Async counterpart; the handler receives one ordinary item dictionary."""
    rows, key_for = _prepare_items(items, key)
    store = SQLiteTaskStore(db_path)
    store.initialize()
    for item in rows:
        store.enqueue(queue, str(key_for(item)), item, max_attempts=max_attempts)

    async def handle(task: Task):
        return await handler(task.payload)

    summary = await AsyncTaskRunner(
        store, logger=logger, retry_delay=retry_delay,
    ).run(queue, handle, limit=limit)
    return summary.as_dict()
