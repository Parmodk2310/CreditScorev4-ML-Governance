#!/usr/bin/env python3
"""Fail closed unless Phase 7 cloud deployment is explicitly enabled."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

REQUIRED_WHEN_ENABLED = ("AWS_ROLE_TO_ASSUME", "AWS_REGION", "TF_STATE_BUCKET", "TF_STATE_KEY")


def is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def evaluate_gate(*, require_confirmation: bool = False) -> tuple[bool, list[str]]:
    if not is_truthy(os.getenv("AWS_DEPLOY_ENABLED")):
        return False, ["AWS_DEPLOY_ENABLED is not true; deployment is blocked by default"]

    missing = [name for name in REQUIRED_WHEN_ENABLED if not os.getenv(name)]
    if require_confirmation and os.getenv("CONFIRM_DEPLOY") != "DEPLOY":
        missing.append("CONFIRM_DEPLOY must equal DEPLOY")
    if missing:
        return False, missing
    return True, []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--require-confirmation", action="store_true")
    args = parser.parse_args()

    enabled, reasons = evaluate_gate(require_confirmation=args.require_confirmation)
    status = "ENABLED" if enabled else "BLOCKED"
    print(f"Phase 7 AWS deployment gate: {status}")
    for reason in reasons:
        print(f"- {reason}")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"enabled={'true' if enabled else 'false'}\n")

    explicitly_requested = is_truthy(os.getenv("AWS_DEPLOY_ENABLED"))
    if explicitly_requested and not enabled:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
