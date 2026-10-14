"""Explicitly configured building blocks; importing this package has no I/O."""

from .config import ProjectPaths, Settings, load_json
from .logging import RunContext
from .workflow import TaskOutcome

from .status import TaskStatus

__version__ = "0.5.2"
__all__ = ["ProjectPaths", "Settings", "load_json", "RunContext", "TaskOutcome", "TaskStatus", "__version__"]
