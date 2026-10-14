"""Business-neutral workflow results.

The task store owns execution status. ``business_state`` belongs to the caller's
workflow, for example ``crawled``, ``matched`` or ``synced``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .status import TaskStatus


@dataclass(frozen=True)
class TaskOutcome:
    """The explicit result of one workflow item."""

    status: TaskStatus = TaskStatus.SUCCEEDED
    result: Any = None
    error: str | None = None
    business_state: str | None = None
    operation_id: str | None = None
    remote_id: str | None = None
    retry_delay: float = 0

    def __post_init__(self):
        object.__setattr__(self, "status", TaskStatus(self.status))
        if self.status == TaskStatus.PROCESSING:
            raise ValueError("TaskOutcome cannot use processing status")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
        if self.business_state is not None and not self.business_state.strip():
            raise ValueError("business_state must be non-empty when supplied")

    @classmethod
    def success(cls, result=None, *, business_state: str | None = None,
                operation_id: str | None = None, remote_id: str | None = None):
        return cls(TaskStatus.SUCCEEDED, result, business_state=business_state,
                   operation_id=operation_id, remote_id=remote_id)

    @classmethod
    def skipped(cls, result=None, *, business_state: str | None = None):
        return cls(TaskStatus.SKIPPED, result, business_state=business_state)

    @classmethod
    def failed(cls, error: str, result=None, *, business_state: str | None = None):
        return cls(TaskStatus.FAILED, result, error=error, business_state=business_state)

    @classmethod
    def manual(cls, error: str, result=None, *, business_state: str | None = None,
               operation_id: str | None = None, remote_id: str | None = None):
        return cls(TaskStatus.NEED_MANUAL, result, error=error, business_state=business_state,
                   operation_id=operation_id, remote_id=remote_id)

    @classmethod
    def retry(cls, error: str | None = None, *, delay: float = 30,
              result=None, business_state: str | None = None):
        return cls(TaskStatus.PENDING, result, error=error, business_state=business_state,
                   retry_delay=delay)
