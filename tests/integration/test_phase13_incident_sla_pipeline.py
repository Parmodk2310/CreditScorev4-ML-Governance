from __future__ import annotations

from creditscore.incident_ops import build_phase13_evidence


def test_phase13_pipeline_produces_expected_sla_and_alert_contract() -> None:
    config = {
        "incident": {
            "incident_id": "CS4-2026-001",
            "source": "vendor_b",
            "scenario": "vendor_b_incident",
            "severity": "HIGH",
            "synthetic": True,
        },
        "timeline": {
            "timezone": "UTC",
            "events": [
                {
                    "event_id": "1",
                    "event_type": "INCIDENT_STARTED",
                    "occurred_at": "2026-01-01T00:00:00+00:00",
                    "source": "vendor_b",
                    "description": "start",
                },
                {
                    "event_id": "2",
                    "event_type": "INCIDENT_DETECTED",
                    "occurred_at": "2026-01-01T03:04:00+00:00",
                    "source": "phase2",
                    "description": "detected",
                },
                {
                    "event_id": "3",
                    "event_type": "ALERT_CREATED",
                    "occurred_at": "2026-01-01T03:05:00+00:00",
                    "source": "phase13",
                    "description": "alert",
                },
                {
                    "event_id": "4",
                    "event_type": "ROOT_CAUSE_COMPLETED",
                    "occurred_at": "2026-01-01T11:30:00+00:00",
                    "source": "phase10",
                    "description": "root cause",
                },
            ],
        },
        "sla": {
            "metrics": [
                {
                    "name": "time_to_detect",
                    "start_event": "INCIDENT_STARTED",
                    "end_event": "INCIDENT_DETECTED",
                    "target_minutes": 240,
                },
                {
                    "name": "time_to_root_cause",
                    "start_event": "INCIDENT_STARTED",
                    "end_event": "ROOT_CAUSE_COMPLETED",
                    "target_minutes": 2880,
                },
            ]
        },
        "alert": {
            "alert_id": "CS4-DQ-VENDOR-B-001",
            "severity": "HIGH",
            "status": "OPEN",
            "source": "phase2_data_quality",
            "signal": "device_risk_score_null_rate",
            "expected_max": 0.05,
            "action": "BLOCK_AND_QUARANTINE",
            "routing": {"mode": "evidence_only", "live_paging": False},
        },
        "safety": {
            "automatic_retraining": False,
            "automatic_promotion": False,
            "live_paging": False,
            "claim_scope": "simulated_incident_sla",
        },
    }

    result = build_phase13_evidence(
        config=config,
        phase2_summary={"incident": {"decision": "BLOCK", "device_risk_null_rate": 0.22}},
        phase9_report={
            "incident": {
                "scenario": "vendor_b_incident",
                "approval_rate": 0.786,
                "approved_default_rate": 0.2637,
            }
        },
        phase10_report={
            "invariants": {
                "generated_combined_matches_vendor_b": True,
                "phase9_consistency": True,
            },
            "scope": {
                "production_policy_changed": False,
                "candidate_selected": False,
            },
        },
        traceability={
            "phase2_summary_sha256": "a" * 64,
            "phase9_report_sha256": "b" * 64,
            "phase10_report_sha256": "c" * 64,
        },
    )

    metrics = {item["name"]: item for item in result["sla"]["metrics"]}
    assert metrics["time_to_detect"]["observed_minutes"] == 184
    assert metrics["time_to_root_cause"]["observed_minutes"] == 690
    assert result["sla"]["all_met"] is True
    assert result["alert"]["routing"]["live_paging"] is False
    assert result["report"]["prior_phase_evidence"]["phase2"]["vendor_b_decision"] == "BLOCK"
