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
    """Load and validate the product-level scoring decision policy."""
    base = Path(root) if root is not None else project_root()
    payload = load_yaml(base / "configs" / "decision_policy.yaml")
    decision = payload.get("decision")
    if not isinstance(decision, dict):
        raise TypeError("Decision policy must define a decision mapping")

    target_column = str(decision.get("target_column", "")).strip()
    if not target_column:
        raise ValueError("Decision policy target_column must be non-empty")

    threshold = float(decision.get("approval_threshold"))
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Decision policy approval_threshold must be between 0 and 1")
    return payload


def decision_settings(root: str | Path | None = None) -> tuple[str, float]:
    """Return the canonical target column and approval threshold."""
    policy = load_decision_policy(root)
    decision = policy["decision"]
    return str(decision["target_column"]), float(decision["approval_threshold"])
