"""Build Phase 13 operational evidence from prior verified phase artifacts."""

from __future__ import annotations

from typing import Any

from .alerting import build_alert_record
from .sla import evaluate_slas
from .timeline import build_timeline


def build_phase13_evidence(
    *,
    config: dict[str, Any],
    phase2_summary: dict[str, Any],
    phase9_report: dict[str, Any],
    phase10_report: dict[str, Any],
    traceability: dict[str, str],
) -> dict[str, Any]:
    events = build_timeline(config)
    alert = build_alert_record(
        config=config,
        events=events,
        phase2_summary=phase2_summary,
    )
    sla_metrics = evaluate_slas(events, list(config["sla"]["metrics"]))

    timeline_payload = {
        "schema_version": 1,
        "phase": 13,
        "incident_id": str(config["incident"]["incident_id"]),
        "synthetic": bool(config["incident"]["synthetic"]),
        "timezone": str(config["timeline"]["timezone"]),
        "events": [event.to_dict() for event in events],
    }

    sla_payload = {
        "schema_version": 1,
        "phase": 13,
        "incident_id": str(config["incident"]["incident_id"]),
        "metrics": [metric.to_dict() for metric in sla_metrics],
        "all_met": all(metric.status == "PASS" for metric in sla_metrics),
        "claim_scope": str(config["safety"]["claim_scope"]),
    }

    phase2_incident = phase2_summary["incident"]
    phase9_incident = phase9_report["incident"]
    phase10_invariants = phase10_report["invariants"]
    phase10_scope = phase10_report["scope"]

    report = {
        "schema_version": 1,
        "phase": 13,
        "name": "incident-sla-operational-evidence",
        "incident": {
            "incident_id": str(config["incident"]["incident_id"]),
            "source": str(config["incident"]["source"]),
            "scenario": str(config["incident"]["scenario"]),
            "severity": str(config["incident"]["severity"]),
            "synthetic": bool(config["incident"]["synthetic"]),
        },
        "prior_phase_evidence": {
            "phase2": {
                "vendor_b_decision": str(phase2_incident["decision"]),
                "device_risk_null_rate": float(phase2_incident["device_risk_null_rate"]),
            },
            "phase9": {
                "scenario": str(phase9_incident.get("scenario", "")),
                "approval_rate": float(phase9_incident["approval_rate"]),
                "approved_default_rate": float(phase9_incident["approved_default_rate"]),
            },
            "phase10": {
                "generated_combined_matches_vendor_b": bool(
                    phase10_invariants["generated_combined_matches_vendor_b"]
                ),
                "phase9_consistency": bool(phase10_invariants["phase9_consistency"]),
                "production_policy_changed": bool(phase10_scope["production_policy_changed"]),
                "candidate_selected": bool(phase10_scope["candidate_selected"]),
            },
        },
        "operational": {
            "alert": alert.to_dict(),
            "sla": sla_payload,
        },
        "safety": {
            "automatic_retraining": bool(config["safety"]["automatic_retraining"]),
            "automatic_promotion": bool(config["safety"]["automatic_promotion"]),
            "live_paging": bool(config["safety"]["live_paging"]),
            "interpretation": (
                "Phase 13 measures a deterministic simulated incident-response timeline. "
                "It does not claim live on-call paging, production MTTR, or a real bank incident."
            ),
        },
        "traceability": traceability,
    }

    return {
        "events": events,
        "timeline": timeline_payload,
        "alert": alert.to_dict(),
        "sla": sla_payload,
        "report": report,
    }
