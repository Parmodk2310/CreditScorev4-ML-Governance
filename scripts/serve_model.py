#!/usr/bin/env python3
"""Run the Phase 6 CreditScoreV4 FastAPI serving process."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import uvicorn

from creditscore.serving.app import create_app
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def apply_environment_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Apply explicit serving overrides without mutating the loaded config."""
    updated = dict(config)
    serving = dict(config["serving"])
    model_path = os.getenv("CREDITSCORE_MODEL_PATH")
    model_digest_path = os.getenv("CREDITSCORE_MODEL_DIGEST_PATH")

    if model_path:
        serving["model_path"] = model_path
        if not model_digest_path:
            model_digest_path = f"{model_path}.sha256"
    if model_digest_path:
        serving["model_digest_path"] = model_digest_path

    updated["serving"] = serving
    return updated


def main() -> int:
    config = apply_environment_overrides(load_yaml(ROOT / "configs" / "phase6.yaml"))
    serving = config["serving"]
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=str(serving["host"]))
    parser.add_argument("--port", type=int, default=int(serving["port"]))
    args = parser.parse_args()

    uvicorn.run(create_app(root=ROOT, config=config), host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
