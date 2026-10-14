from __future__ import annotations

import copy
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable
from uuid import uuid4


def safe_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise ValueError("Name must contain 1-80 ASCII letters, digits, '_' or '-'")
    return value


class RedactingFormatter(logging.Formatter):
    def __init__(self, secrets: Iterable[str] = ()):
        super().__init__(
            "%(asctime)s | %(levelname)s | project=%(project)s run=%(run_id)s "
            "stage=%(stage)s shop=%(shop)s task=%(task_id)s | %(message)s"
        )
        self.secrets = sorted({value for value in secrets if value}, key=len, reverse=True)

    def format(self, record):
        cloned = copy.copy(record)
        cloned.exc_text = None
        output = super().format(cloned)
        for secret in self.secrets:
            output = output.replace(secret, "[REDACTED]")
        return output


class BoundLogger(logging.LoggerAdapter):
    def process(self, message, kwargs):
        kwargs["extra"] = {**self.extra, **kwargs.get("extra", {})}
        return message, kwargs

    def bind(self, **fields) -> BoundLogger:
        return BoundLogger(self.logger, {**self.extra, **fields})


class RunContext:
    """One run, one UTF-8 log; no changes to the process-wide root logger."""

    def __init__(
        self, project: str, log_dir: str | Path, *,
        secrets: Iterable[str] = (), console: bool = True, level: int = logging.INFO,
    ):
        self.project = safe_name(project)
        self.log_dir = Path(log_dir)
        self.secrets = tuple(secrets)
        self.console = console
        self.level = level
        self.run_id = uuid4().hex
        self.log_file: Path | None = None
        self.logger: BoundLogger
        self._logger: logging.Logger | None = None
        self._entered = False

    def __enter__(self) -> RunContext:
        if self._entered:
            raise RuntimeError("RunContext can only be entered once")
        self._entered = True
        now = datetime.now()
        directory = self.log_dir / now.strftime("%Y-%m-%d")
        directory.mkdir(parents=True, exist_ok=True)
        self.log_file = directory / f"{self.project}_{now:%H%M%S}_{self.run_id}.log"
        logger = logging.Logger(f"{self.project}.{self.run_id}", self.level)
        logger.propagate = False
        formatter = RedactingFormatter(self.secrets)
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        if self.console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        self._logger = logger
        self.logger = BoundLogger(logger, {
            "project": self.project, "run_id": self.run_id,
            "stage": "-", "shop": "-", "task_id": "-",
        })
        self.logger.info("run_started")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.logger.info("run_finished")
            else:
                self.logger.error("run_failed", exc_info=(exc_type, exc_value, traceback))
        finally:
            self.close()
        return False

    def close(self) -> None:
        if self._logger is not None:
            for handler in list(self._logger.handlers):
                self._logger.removeHandler(handler)
                handler.close()
