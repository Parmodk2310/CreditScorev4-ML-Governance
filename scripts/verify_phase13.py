#!/usr/bin/env python3
"""Verify Phase 13 incident timeline, alert, SLA, and cross-phase lineage."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from creditscore.utils.config import load_yaml
from creditscore.utils.hashing import file_sha256

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_EVENTS = {
    "INCIDENT_STARTED",
    "BATCH_INGESTED",
    "DATA_QUALITY_CHECK_STARTED",
    "INCIDENT_DETECTED",
    "ALERT_CREATED",
    "GOVERNANCE_BLOCKED",
    "TRIAGE_STARTED",
    "ROOT_CAUSE_COMPLETED",
    "INCIDENT_REVIEW_COMPLETED",
}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return payload


def _parse(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"Timestamp must be timezone-aware: {value}")
    return timestamp


def main() -> int:
    config = load_yaml(ROOT / "configs" / "phase13.yaml")
    evidence = config["evidence"]
    acceptance = config["acceptance"]

    paths = {
        name: ROOT / str(evidence[name])
        for name in (
            "data_contract",
            "phase2_summary",
            "phase9_report",
            "phase10_report",
            "timeline",
            "events",
            "alert",
            "sla_summary",
            "incident_report",
        )
    }

    missing = [path for path in paths.values() if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing Phase 13 evidence: {path.relative_to(ROOT)}")
        return 1

    contract = load_yaml(paths["data_contract"])
    phase2 = _read_json(paths["phase2_summary"])
    phase9 = _read_json(paths["phase9_report"])
    phase10 = _read_json(paths["phase10_report"])
    timeline = _read_json(paths["timeline"])
    alert = _read_json(paths["alert"])
    sla = _read_json(paths["sla_summary"])
    report = _read_json(paths["incident_report"])

    events = timeline["events"]
    event_types = {str(event["event_type"]) for event in events}
    event_times = [_parse(str(event["occurred_at"])) for event in events]
    by_type = {str(event["event_type"]): event for event in events}
    incident_id = str(config["incident"]["incident_id"])

    metrics = {str(item["name"]): item for item in sla["metrics"]}

    expected_minutes = {
        "time_to_detect": int(acceptance["expected_detection_minutes"]),
        "time_to_alert": int(acceptance["expected_alert_minutes"]),
        "time_to_block": int(acceptance["expected_block_minutes"]),
        "time_to_triage": int(acceptance["expected_triage_minutes"]),
        "time_to_root_cause": int(acceptance["expected_root_cause_minutes"]),
    }

    event_lines = [
        json.loads(line) for line in paths["events"].read_text(encoding="utf-8").splitlines() if line.strip()
    ]

    traceability = report["traceability"]
    hash_matches = (
        traceability.get("data_contract_sha256") == file_sha256(paths["data_contract"])
        and traceability.get("phase2_summary_sha256") == file_sha256(paths["phase2_summary"])
        and traceability.get("phase9_report_sha256") == file_sha256(paths["phase9_report"])
        and traceability.get("phase10_report_sha256") == file_sha256(paths["phase10_report"])
    )

    gates = {
        "incident_id_consistent": (
            timeline["incident_id"] == incident_id
            and alert["incident_id"] == incident_id
            and sla["incident_id"] == incident_id
            and report["incident"]["incident_id"] == incident_id
        ),
        "timeline_sorted": event_times == sorted(event_times),
        "timestamps_timezone_aware": all(value.tzinfo is not None for value in event_times),
        "required_events_present": REQUIRED_EVENTS <= event_types,
        "phase2_vendor_b_blocked": str(phase2["incident"]["decision"]) == "BLOCK",
        "phase9_vendor_b_scenario": str(phase9["incident"].get("scenario", "")) == "vendor_b_incident",
        "phase10_vendor_b_consistency": (
            bool(phase10["invariants"]["generated_combined_matches_vendor_b"])
            and bool(phase10["invariants"]["phase9_consistency"])
            and phase10["scope"]["production_policy_changed"] is False
            and phase10["scope"]["candidate_selected"] is False
        ),
        "traceability_hashes_match": hash_matches,
        "events_jsonl_matches_timeline": event_lines == events,
        "alert_threshold_matches_contract": (
            abs(
                float(alert["expected_max"])
                - float(contract["columns"]["device_risk_score"]["max_null_rate"])
            )
            < 1e-12
        ),
        "alert_created_after_detection": (
            _parse(by_type["ALERT_CREATED"]["occurred_at"])
            > _parse(by_type["INCIDENT_DETECTED"]["occurred_at"])
        ),
        "block_after_detection": (
            _parse(by_type["GOVERNANCE_BLOCKED"]["occurred_at"])
            > _parse(by_type["INCIDENT_DETECTED"]["occurred_at"])
        ),
        "triage_after_detection": (
            _parse(by_type["TRIAGE_STARTED"]["occurred_at"])
            > _parse(by_type["INCIDENT_DETECTED"]["occurred_at"])
        ),
        "root_cause_after_triage": (
            _parse(by_type["ROOT_CAUSE_COMPLETED"]["occurred_at"])
            > _parse(by_type["TRIAGE_STARTED"]["occurred_at"])
        ),
        "all_slas_pass": bool(sla["all_met"])
        and all(str(item["status"]) == "PASS" for item in sla["metrics"]),
        "sla_minutes_exact": all(
            name in metrics and int(metrics[name]["observed_minutes"]) == expected
            for name, expected in expected_minutes.items()
        ),
        "root_cause_within_48h": (
            int(metrics["time_to_root_cause"]["target_minutes"]) == 2880
            and int(metrics["time_to_root_cause"]["observed_minutes"]) <= 2880
        ),
        "alert_matches_incident_signal": (
            alert["signal"] == "device_risk_score_null_rate"
            and abs(float(alert["observed"]) - float(phase2["incident"]["device_risk_null_rate"])) < 1e-12
            and alert["action"] == "BLOCK_AND_QUARANTINE"
        ),
        "alert_is_simulated": alert["synthetic"] is True,
        "live_paging_disabled": alert["routing"]["live_paging"] is False
        and report["safety"]["live_paging"] is False,
        "automatic_retraining_disabled": report["safety"]["automatic_retraining"] is False,
        "automatic_promotion_disabled": report["safety"]["automatic_promotion"] is False,
    }

    print("CreditScoreV4 — Phase 13 Verification")
    print("=" * 41)
    print(f"  incident id...................... {incident_id}")
    print(f"  detection latency................ {metrics['time_to_detect']['observed_minutes']} min")
    print(f"  alert latency.................... {metrics['time_to_alert']['observed_minutes']} min")
    print(f"  block latency.................... {metrics['time_to_block']['observed_minutes']} min")
    print(f"  root-cause completion............ {metrics['time_to_root_cause']['observed_minutes']} min")
    print()
    print("Acceptance gates")
    for name, passed in gates.items():
        print(f"  {name:<42} {'PASS' if passed else 'FAIL'}")

    if all(gates.values()):
        print("\nPHASE 13 CORE: VERIFIED")
        print(
            "Simulated incident SLA evidence passes; live paging, automatic retraining, "
            "and automatic promotion remain disabled."
        )
        return 0

    print("\nPHASE 13: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
