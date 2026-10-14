from enum import Enum


class TaskStatus(str, Enum):
    """Execution status owned by the foundation package."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEED_MANUAL = "need_manual"
