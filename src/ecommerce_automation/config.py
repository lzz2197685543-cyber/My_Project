from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from ._optional import require
from .errors import ConfigError


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    def __post_init__(self):
        object.__setattr__(self, "root", Path(self.root).resolve())

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    def ensure_runtime(self) -> None:
        self.data.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)


def load_json(path: str | Path) -> dict[str, Any]:
    try:
        result = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise ConfigError(f"Cannot read JSON configuration: {path}") from error
    if not isinstance(result, dict):
        raise ConfigError(f"Configuration must be a JSON object: {path}")
    return result


@dataclass(frozen=True)
class Settings:
    values: Mapping[str, str] = field(repr=False)

    def __post_init__(self):
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    @classmethod
    def load(
        cls, *, env_file: str | Path | None = None,
        defaults: Mapping[str, str] | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> Settings:
        values = dict(defaults or {})
        if env_file is not None:
            path = Path(env_file)
            if not path.is_file():
                raise ConfigError(f"Missing environment file: {path}")
            dotenv = require("dotenv", "config")
            values.update({
                key: value for key, value in dotenv.dotenv_values(
                    path, encoding="utf-8-sig", interpolate=False
                ).items() if value is not None
            })
        values.update(os.environ if environ is None else environ)
        return cls(values)

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.values.get(key, default)

    def require(self, key: str) -> str:
        value = self.get(key)
        if value is None or not value.strip():
            raise ConfigError(f"Missing required setting: {key}")
        return value

    def integer(self, key: str, default: int | None = None, *, minimum: int | None = None) -> int:
        raw = self.get(key)
        try:
            value = int(raw) if raw is not None else default
        except ValueError:
            raise ConfigError(f"Setting {key} must be an integer") from None
        if value is None or (minimum is not None and value < minimum):
            raise ConfigError(f"Setting {key} must be an integer >= {minimum}")
        return value

    def boolean(self, key: str, default: bool = False) -> bool:
        raw = self.get(key)
        if raw is None:
            return default
        normalized = raw.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ConfigError(f"Setting {key} must be a boolean")
