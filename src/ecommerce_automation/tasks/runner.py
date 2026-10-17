from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Any
from uuid import uuid4

from ..errors import AuthenticationError, PermanentError, RetryableError, SkipTask
from ..status import TaskStatus
from ..workflow import TaskOutcome
from .store import SQLiteTaskStore, Task, TaskStore

# ============================================================
# TaskRunner.run() 执行流程
#
# 1. 从数据库领取任务
#    task = store.claim(queue, worker_id, lease_seconds=...)
#    - 从指定队列领取一个可执行任务
#    - 如果没有可领取的任务，则退出循环
#
# 2. 执行业务处理函数
#    result = handler(task)
#    - 执行采集、匹配、同步等具体业务逻辑
#
# 3. 判断业务执行结果
#    - 正常返回：
#        调用 _finish_result() 处理业务结果
#    - 抛出异常：
#        调用 _record_error() 根据异常类型分类处理
#        SkipTask        -> SKIPPED
#        RetryableError  -> PENDING
#        PermanentError  -> FAILED
#        其他异常         -> NEED_MANUAL
#
# 4. 更新数据库任务状态
#    store.finish(...)
#    - 保存任务状态、执行结果、错误信息
#


@dataclass
class RunSummary:
    claimed: int = 0
    outcomes: dict[str, int] = field(default_factory=lambda: {status.value: 0 for status in TaskStatus})

    def as_dict(self) -> dict:
        return {"claimed": self.claimed, **self.outcomes}


class TaskRunner:
    """Sequential local runner. Handlers must confirm the business result before returning."""

    def __init__(
        self, store: TaskStore, *, logger: Any = None,
        worker_id: str | None = None, lease_seconds: float = 300, retry_delay: float = 30,
    ):
        if lease_seconds <= 0 or retry_delay < 0:
            raise ValueError("Invalid lease_seconds/retry_delay")
        self.store = store
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.worker_id = worker_id or uuid4().hex
        self.lease_seconds = lease_seconds
        self.retry_delay = retry_delay

    def _record_error(self, task: Task, error: Exception) -> TaskStatus:
        if isinstance(error, SkipTask):
            requested = TaskStatus.SKIPPED
        elif isinstance(error, RetryableError):
            requested = TaskStatus.PENDING
        elif isinstance(error, PermanentError):
            requested = TaskStatus.FAILED
        else:
            requested = TaskStatus.NEED_MANUAL
        return self.store.finish(
            task, requested, error=f"{type(error).__name__}: {error}",
            retry_delay=self.retry_delay,
        )

    def _finish_result(self, task: Task, result: Any) -> TaskStatus:
        outcome = result if isinstance(result, TaskOutcome) else TaskOutcome.success(result)
        return self.store.finish(
            task, outcome.status, result=outcome.result, error=outcome.error,
            retry_delay=outcome.retry_delay, business_state=outcome.business_state,
            operation_id=outcome.operation_id, remote_id=outcome.remote_id,
        )

    def run(self, queue: str, handler: Callable[[Task], Any], *, limit: int = 100) -> RunSummary:
        if limit < 1 or inspect.iscoroutinefunction(handler):
            raise ValueError("Use a synchronous handler and a positive limit")
        summary = RunSummary()
        for _ in range(limit):
            task = self.store.claim(queue, self.worker_id, lease_seconds=self.lease_seconds)
            if task is None:
                break
            summary.claimed += 1
            stop = False
            try:
                result = handler(task)
                if inspect.isawaitable(result):
                    if inspect.iscoroutine(result):
                        result.close()
                    raise TypeError("Handler returned an awaitable; TaskRunner requires sync handlers")
            except Exception as error:
                stop = isinstance(error, AuthenticationError)
                status = self._record_error(task, error)
            else:
                status = self._finish_result(task, result)
            summary.outcomes[status.value] += 1
            self.logger.info("task_finished status=%s key=%s", status.value, task.key, extra={"task_id": task.id})
            if stop:
                break
        self.logger.info("batch_finished summary=%s", summary.as_dict())
        return summary


class AsyncTaskRunner(TaskRunner):
    """Sequential async runner; blocking SQLite operations execute in a worker thread."""

    async def run(self, queue: str, handler: Callable[[Task], Awaitable[Any]], *, limit: int = 100) -> RunSummary:
        if limit < 1:
            raise ValueError("limit must be positive")
        summary = RunSummary()
        for _ in range(limit):
            task = await asyncio.to_thread(
                self.store.claim, queue, self.worker_id, lease_seconds=self.lease_seconds,
            )
            if task is None:
                break
            summary.claimed += 1
            stop = False
            try:
                result = await handler(task)
            except Exception as error:
                stop = isinstance(error, AuthenticationError)
                status = await asyncio.to_thread(self._record_error, task, error)
            else:
                status = await asyncio.to_thread(
                    self._finish_result, task, result,
                )
            summary.outcomes[status.value] += 1
            self.logger.info("task_finished status=%s key=%s", status.value, task.key, extra={"task_id": task.id})
            if stop:
                break
        self.logger.info("batch_finished summary=%s", summary.as_dict())
        return summary



