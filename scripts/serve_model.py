#!/usr/bin/env python3
"""Run the Phase 6 CreditScoreV4 FastAPI serving process."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from creditscore.serving.app import create_app
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase6.yaml")
    serving = config["serving"]
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=str(serving["host"]))
    parser.add_argument("--port", type=int, default=int(serving["port"]))
    args = parser.parse_args()

    uvicorn.run(create_app(root=ROOT, config=config), host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
