#!/usr/bin/env python3
"""Static/local acceptance gate for Phase 7 automation and deployment."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from check_deployment_gate import evaluate_gate
from write_release_manifest import build_manifest

ROOT = Path(__file__).resolve().parents[1]
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def contains(path: str, *tokens: str) -> bool:
    text = (ROOT / path).read_text(encoding="utf-8")
    return all(token in text for token in tokens)


def workflow_actions_are_pinned(path: str) -> bool:
    text = (ROOT / path).read_text(encoding="utf-8")
    refs: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- uses:"):
            continue
        value = stripped.split("uses:", 1)[1].split("#", 1)[0].strip()
        if "@" not in value:
            return False
        _, ref = value.rsplit("@", 1)
        refs.append(ref)
    return bool(refs) and all(SHA_PATTERN.fullmatch(ref) for ref in refs)


def main() -> int:
    original = os.environ.pop("AWS_DEPLOY_ENABLED", None)
    try:
        enabled, _ = evaluate_gate()
    finally:
        if original is not None:
            os.environ["AWS_DEPLOY_ENABLED"] = original

    manifest_path = ROOT / "data/evidence/phase7/release_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest("sha256:phase7-verification", False)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    gates = {
        "ci_workflow": (
            contains(".github/workflows/ci.yml", "make quality", "terraform validate")
            and workflow_actions_are_pinned(".github/workflows/ci.yml")
        ),
        "security_workflow": (
            contains(
                ".github/workflows/security.yml",
                "gitleaks/gitleaks-action@",
                "aquasecurity/trivy-action@",
            )
            and workflow_actions_are_pinned(".github/workflows/security.yml")
        ),
        "image_workflow": (
            contains(
                ".github/workflows/image.yml",
                "docker/build-push-action@",
                "verify_container.py",
            )
            and workflow_actions_are_pinned(".github/workflows/image.yml")
        ),
        "deploy_fail_closed": enabled is False,
        "deploy_workflow_oidc": (
            contains(
                ".github/workflows/deploy.yml",
                "id-token: write",
                "AWS_DEPLOY_ENABLED",
                "aws-actions/configure-aws-credentials@",
            )
            and workflow_actions_are_pinned(".github/workflows/deploy.yml")
        ),
        "persistent_state": contains(
            ".github/workflows/deploy.yml",
            "TF_STATE_BUCKET",
            "use_lockfile=true",
        ),
        "ecr_immutable": contains(
            "infra/terraform/ecr.tf",
            'image_tag_mutability = "IMMUTABLE"',
            "scan_on_push = true",
        ),
        "ecs_fargate": contains(
            "infra/terraform/ecs.tf",
            'requires_compatibilities = ["FARGATE"]',
            "aws_ecs_service",
        ),
        "alb_health_check": contains(
            "infra/terraform/ecs.tf",
            'path                = "/health"',
        ),
        "service_ingress_restricted": contains(
            "infra/terraform/networking.tf",
            "security_groups = [aws_security_group.alb.id]",
        ),
        "release_manifest_written": (manifest_path.exists() and manifest["deployment_enabled"] is False),
    }

    print("CreditScoreV4 — Phase 7 Verification")
    print("=" * 41)
    for name, passed in gates.items():
        print(f"  {name:<34} {'PASS' if passed else 'FAIL'}")

    if not all(gates.values()):
        return 1

    print("\nAWS_DEPLOY_ENABLED................ false (safe default)")
    print("PHASE 7: VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
