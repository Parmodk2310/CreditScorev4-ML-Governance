#!/usr/bin/env python3
"""Advance a healthy Phase 6 canary through configured rollout checkpoints."""

from __future__ import annotations

from pathlib import Path

from creditscore.release.controller import SafeReleaseController
from creditscore.release.models import ReleaseHealthSnapshot
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase6.yaml")
    controller = SafeReleaseController.from_config(root=ROOT, config=config)
    while True:
        state = controller.advance_canary(
            ReleaseHealthSnapshot(
                request_count=500,
                error_rate=0.004,
                p95_latency_ms=55.0,
                mean_risk_delta=0.01,
            )
        )
        print(
            f"Stage={state.stage} share={state.canary_share:.0%} "
            f"completed={','.join(f'{share:.0%}' for share in state.completed_shares)}"
        )
        if state.stage != "CANARY":
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
