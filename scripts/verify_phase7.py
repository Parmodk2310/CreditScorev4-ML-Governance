#!/usr/bin/env python3
"""Static/local acceptance gate for Phase 7 automation and deployment."""

from __future__ import annotations

import json
import os
from pathlib import Path

from check_deployment_gate import evaluate_gate
from write_release_manifest import build_manifest

ROOT = Path(__file__).resolve().parents[1]


def contains(path: str, *tokens: str) -> bool:
    text = (ROOT / path).read_text(encoding="utf-8")
    return all(token in text for token in tokens)


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
        "ci_workflow": contains(
            ".github/workflows/ci.yml",
            "make quality",
            "terraform validate",
        ),
        "security_workflow": contains(
            ".github/workflows/security.yml",
            "gitleaks/gitleaks-action@v3",
            "aquasecurity/trivy-action@v0.36.0",
        ),
        "image_workflow": contains(
            ".github/workflows/image.yml",
            "docker/build-push-action@v7",
            "verify_container.py",
        ),
        "deploy_fail_closed": enabled is False,
        "deploy_workflow_oidc": contains(
            ".github/workflows/deploy.yml",
            "id-token: write",
            "AWS_DEPLOY_ENABLED",
            "configure-aws-credentials@v6",
        ),
        "persistent_state": contains(".github/workflows/deploy.yml", "TF_STATE_BUCKET", "use_lockfile=true"),
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
        "alb_health_check": contains("infra/terraform/ecs.tf", 'path                = "/health"'),
        "service_ingress_restricted": contains(
            "infra/terraform/networking.tf",
            "security_groups = [aws_security_group.alb.id]",
        ),
        "release_manifest_written": manifest_path.exists() and manifest["deployment_enabled"] is False,
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
