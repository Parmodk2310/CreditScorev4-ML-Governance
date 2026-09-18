"""Configuration helpers for Phase 1."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else project_root() / "configs" / "phase1.yaml"
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
