#!/usr/bin/env python3
"""Phase 6 release gate: API serving, observability, shadow/canary, and rollback."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.governance.registry import ModelRegistry, RegistryTransitionError
from creditscore.release.controller import SafeReleaseController
from creditscore.release.models import ReleaseHealthSnapshot
from creditscore.release.router import CanaryRouter
from creditscore.serving.app import create_app
from creditscore.serving.predictor import ModelPredictor
from creditscore.utils.config import load_yaml
from creditscore.utils.hashing import file_sha256

ROOT = Path(__file__).resolve().parents[1]
ROLLBACK_VERSION = "0.6.0-rollback-check"
ILLEGAL_VERSION = "0.6.0-illegal-release-check"


def _ensure_phase5_staging(config: dict) -> None:
    registry = ModelRegistry(ROOT / config["release"]["registry_path"])
    try:
        record = registry.get(str(config["release"]["model_name"]), str(config["release"]["model_version"]))
    except (FileNotFoundError, KeyError, ValueError):
        record = None
    if record is None or record.stage != "STAGING":
        subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_phase5.py")], check=True)


def _reset_phase6(config: dict) -> None:
    for key in ("audit_log", "state_path"):
        path = ROOT / str(config["release"][key])
        if path.exists():
            path.unlink()
    evidence_dir = ROOT / str(config["paths"]["evidence_dir"])
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for child in evidence_dir.iterdir():
        if child.name != ".gitkeep" and child.is_file():
            child.unlink()


def _records(limit: int) -> list[dict]:
    frame = pd.read_csv(ROOT / "data" / "raw" / "vendor_a" / "holdout.csv").head(limit)
    records: list[dict] = []
    for _, row in frame.iterrows():
        record = {column: row[column] for column in MODEL_INPUT_FEATURES}
        record["application_id"] = str(row["application_id"])
        if pd.isna(record["device_risk_score"]):
            record["device_risk_score"] = None
        for key, value in list(record.items()):
            if hasattr(value, "item"):
                record[key] = value.item()
        records.append(record)
    return records


def _stage_new_version(config: dict, version: str, scenario: str) -> None:
    release = config["release"]
    registry = ModelRegistry(ROOT / str(release["registry_path"]))
    model_path = ROOT / str(config["serving"]["model_path"])
    record = registry.register(
        model_name=str(release["model_name"]),
        version=version,
        artifact_path=str(model_path),
        artifact_sha256=file_sha256(model_path),
        metadata={"scenario": scenario},
    )
    if record.stage == "REGISTERED":
        record = registry.transition(
            model_name=record.model_name,
            version=record.version,
            target_stage="CANDIDATE",
        )
    if record.stage == "CANDIDATE":
        registry.transition(model_name=record.model_name, version=record.version, target_stage="STAGING")


def _routing_is_accurate(shares: list[float]) -> tuple[bool, dict[str, float]]:
    observed: dict[str, float] = {}
    keys = [f"request-{index:05d}" for index in range(5000)]
    passed = True
    for share in shares:
        router = CanaryRouter(share)
        candidate = sum(router.route(key) == "candidate" for key in keys)
        fraction = candidate / len(keys)
        observed[f"{share:.2f}"] = fraction
        if not math.isclose(fraction, share, abs_tol=0.03):
            passed = False
    return passed, observed


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase6.yaml")
    _ensure_phase5_staging(config)
    _reset_phase6(config)

    serving = config["serving"]
    predictor = ModelPredictor(
        model_path=ROOT / str(serving["model_path"]),
        model_name=str(serving["model_name"]),
        model_version=str(serving["model_version"]),
        decision_threshold=float(serving["decision_threshold"]),
    )
    app = create_app(root=ROOT, config=config, predictor=predictor)
    sample_records = _records(200)
    with TestClient(app) as client:
        health_response = client.get("/health")
        ready_response = client.get("/ready")
        model_response = client.get("/model")
        predict_response = client.post("/predict", json=sample_records[0])
        batch_response = client.post("/batch-predict", json={"applications": sample_records[:5]})
        metrics_response = client.get("/metrics")

    baseline = predictor.predict_batch(sample_records)
    candidate = predictor.predict_batch(sample_records)
    mean_risk_delta = sum(
        abs(left.risk_probability - right.risk_probability)
        for left, right in zip(baseline, candidate, strict=True)
    ) / len(baseline)

    controller = SafeReleaseController.from_config(root=ROOT, config=config)
    shadow_state = controller.start_shadow()
    canary_state = controller.complete_shadow(
        ReleaseHealthSnapshot(
            request_count=len(sample_records),
            error_rate=0.0,
            p95_latency_ms=45.0,
            mean_risk_delta=mean_risk_delta,
        )
    )
    visited_shares: list[float] = []
    while canary_state.stage == "CANARY":
        visited_shares.append(canary_state.canary_share)
        canary_state = controller.advance_canary(
            ReleaseHealthSnapshot(
                request_count=500,
                error_rate=0.004,
                p95_latency_ms=55.0,
                mean_risk_delta=0.01,
            )
        )
    production_state = canary_state

    _stage_new_version(config, ROLLBACK_VERSION, "degraded_canary")
    rollback_controller = SafeReleaseController.from_config(
        root=ROOT,
        config=config,
        model_version=ROLLBACK_VERSION,
    )
    rollback_controller.start_shadow()
    rollback_controller.complete_shadow(ReleaseHealthSnapshot(200, 0.001, 40.0, 0.0))
    rollback_state = rollback_controller.advance_canary(ReleaseHealthSnapshot(500, 0.09, 480.0, 0.15))

    release = config["release"]
    registry = ModelRegistry(ROOT / str(release["registry_path"]))
    model_path = ROOT / str(serving["model_path"])
    illegal = registry.register(
        model_name=str(release["model_name"]),
        version=ILLEGAL_VERSION,
        artifact_path=str(model_path),
        artifact_sha256=file_sha256(model_path),
        metadata={"scenario": "illegal_direct_production"},
    )
    if illegal.stage == "REGISTERED":
        illegal = registry.transition(
            model_name=illegal.model_name,
            version=illegal.version,
            target_stage="CANDIDATE",
        )
    illegal_transition_blocked = False
    try:
        registry.transition(model_name=illegal.model_name, version=illegal.version, target_stage="PRODUCTION")
    except RegistryTransitionError:
        illegal_transition_blocked = True

    routing_passed, routing_observed = _routing_is_accurate([float(v) for v in release["canary_shares"]])
    audit_records = controller.audit.read_all()
    acceptance = config["acceptance"]
    metrics_text = metrics_response.text
    gates = {
        "health_endpoint": health_response.status_code == 200 and health_response.json()["status"] == "ok",
        "ready_endpoint": ready_response.status_code == 200 and ready_response.json()["model_ready"] is True,
        "model_endpoint": model_response.status_code == 200
        and bool(model_response.json()["artifact_sha256"]),
        "predict_endpoint": predict_response.status_code == 200
        and 0.0 <= predict_response.json()["risk_probability"] <= 1.0,
        "batch_predict_endpoint": batch_response.status_code == 200 and batch_response.json()["count"] == 5,
        "metrics_endpoint": metrics_response.status_code == 200
        and "creditscore_http_requests_total" in metrics_text,
        "shadow_started": shadow_state.stage == "SHADOW",
        "shadow_promoted_to_canary": bool(visited_shares),
        "configured_canary_shares_exercised": visited_shares == [float(v) for v in release["canary_shares"]],
        "deterministic_canary_routing": routing_passed,
        "healthy_rollout_reaches_production": production_state.stage
        == str(acceptance["healthy_final_stage"]),
        "degraded_canary_rolls_back": rollback_state.stage == str(acceptance["rollback_final_stage"]),
        "rollback_reason_written": bool(rollback_state.rollback_reason),
        "illegal_direct_production_blocked": illegal_transition_blocked,
        "release_audit_written": len(audit_records) >= int(acceptance["minimum_release_audit_records"]),
    }

    report = {
        "healthy_model_version": str(release["model_version"]),
        "healthy_final_stage": production_state.stage,
        "visited_canary_shares": visited_shares,
        "routing_observed": routing_observed,
        "rollback_model_version": ROLLBACK_VERSION,
        "rollback_final_stage": rollback_state.stage,
        "rollback_reason": rollback_state.rollback_reason,
        "audit_records": len(audit_records),
        "acceptance_gates": gates,
    }
    evidence_path = ROOT / str(config["paths"]["evidence_dir"]) / "phase6_release_report.json"
    evidence_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    gates["release_evidence_written"] = evidence_path.exists()

    print("CreditScoreV4 — Phase 6 Verification")
    print("=" * 41)
    print("Serving API")
    print(f"  /health.................... {health_response.status_code}")
    print(f"  /ready..................... {ready_response.status_code}")
    print(f"  /predict................... {predict_response.status_code}")
    print(f"  /batch-predict............. {batch_response.status_code}")
    print(f"  /model..................... {model_response.status_code}")
    print(f"  /metrics................... {metrics_response.status_code}")
    print()
    print("Healthy release")
    print(f"  Shadow..................... {shadow_state.stage}")
    print(f"  Canary checkpoints......... {', '.join(f'{value:.0%}' for value in visited_shares)}")
    print(f"  Final stage................ {production_state.stage}")
    print()
    print("Degraded release")
    print(f"  Final stage................ {rollback_state.stage}")
    print(f"  Rollback reason............ {rollback_state.rollback_reason}")
    print()
    print(f"Release audit records......... {len(audit_records)}")
    print("Acceptance gates")
    for name, passed in gates.items():
        print(f"  {name:38} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 6: VERIFIED")
        return 0
    print("\nPHASE 6: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
