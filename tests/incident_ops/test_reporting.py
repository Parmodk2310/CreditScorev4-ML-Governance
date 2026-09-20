from __future__ import annotations

from creditscore.incident_ops import build_phase13_evidence


def _config() -> dict:
    return {
        "incident": {
            "incident_id": "INC-1",
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
                    "event_type": "ALERT_CREATED",
                    "occurred_at": "2026-01-01T00:05:00+00:00",
                    "source": "phase13",
                    "description": "alert",
                },
            ],
        },
        "sla": {
            "metrics": [
                {
                    "name": "time_to_alert",
                    "start_event": "INCIDENT_STARTED",
                    "end_event": "ALERT_CREATED",
                    "target_minutes": 10,
                }
            ]
        },
        "alert": {
            "alert_id": "A-1",
            "severity": "HIGH",
            "status": "OPEN",
            "source": "phase2",
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


def test_report_links_prior_phase_evidence_and_safety_boundaries() -> None:
    result = build_phase13_evidence(
        config=_config(),
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

    assert result["report"]["prior_phase_evidence"]["phase2"]["vendor_b_decision"] == "BLOCK"
    assert result["report"]["safety"]["automatic_retraining"] is False
    assert result["report"]["safety"]["automatic_promotion"] is False
    assert result["sla"]["all_met"] is True
