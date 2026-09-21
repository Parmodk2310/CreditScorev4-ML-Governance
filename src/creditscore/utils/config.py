"""Project configuration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_yaml(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected mapping in YAML file: {config_path}")
    return payload


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else project_root() / "configs" / "phase1.yaml"
    return load_yaml(config_path)


def load_decision_policy(root: str | Path | None = None) -> dict[str, Any]:
    """Load the canonical product-level decision policy."""
    base = Path(root) if root is not None else project_root()
    return load_yaml(base / "configs" / "decision_policy.yaml")


def decision_threshold(root: str | Path | None = None) -> float:
    """Return the canonical approval/default decision threshold."""
    policy = load_decision_policy(root)
    return float(policy["decision"]["approval_threshold"])


def decision_target_column(root: str | Path | None = None) -> str:
    """Return the canonical prediction target column."""
    policy = load_decision_policy(root)
    return str(policy["decision"]["target_column"])
