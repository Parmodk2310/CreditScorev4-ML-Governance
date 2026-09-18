#!/usr/bin/env python3
"""Start and evaluate a healthy Phase 6 shadow checkpoint."""

from __future__ import annotations

from pathlib import Path

from creditscore.release.controller import SafeReleaseController
from creditscore.release.models import ReleaseHealthSnapshot
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase6.yaml")
    controller = SafeReleaseController.from_config(root=ROOT, config=config)
    state = controller.start_shadow()
    print(f"Shadow started: {state.model_version} -> {state.stage}")
    state = controller.complete_shadow(
        ReleaseHealthSnapshot(
            request_count=200,
            error_rate=0.001,
            p95_latency_ms=45.0,
            mean_risk_delta=0.0,
        )
    )
    print(f"Shadow decision: {state.stage}; next canary share={state.canary_share:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
