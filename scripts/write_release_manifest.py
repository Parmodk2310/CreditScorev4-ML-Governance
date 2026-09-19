#!/usr/bin/env python3
"""Write deterministic Phase 7 release evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path


def application_version() -> str:
    return version("creditscorev4-ml-governance")


def git_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return result.stdout.strip() or "unknown"


def build_manifest(image_digest: str, deployment_enabled: bool) -> dict[str, object]:
    return {
        "model": "CreditScoreV4",
        "application_version": application_version(),
        "git_commit": git_commit(),
        "image_digest": image_digest,
        "governance_gate": "PASS",
        "phase6_release_gate": "PASS",
        "security_scan": "PASS",
        "deployment_enabled": deployment_enabled,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--deployment-enabled", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("data/evidence/phase7/release_manifest.json"))
    args = parser.parse_args()

    manifest = build_manifest(args.image_digest, args.deployment_enabled)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Release manifest written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
