"""Synthetic alert evidence generation for Phase 13."""

from __future__ import annotations

from typing import Any

from .models import AlertRecord, IncidentEvent
from .timeline import event_map


def build_alert_record(
    *,
    config: dict[str, Any],
    events: list[IncidentEvent],
    phase2_summary: dict[str, Any],
) -> AlertRecord:
    alert_config = config["alert"]
    incident_config = config["incident"]
    by_type = event_map(events)

    if "ALERT_CREATED" not in by_type:
        raise ValueError("ALERT_CREATED event is required")

    incident = phase2_summary.get("incident", {})
    observed = float(incident["device_risk_null_rate"])

    return AlertRecord(
        alert_id=str(alert_config["alert_id"]),
        incident_id=str(incident_config["incident_id"]),
        severity=str(alert_config["severity"]),
        status=str(alert_config["status"]),
        source=str(alert_config["source"]),
        signal=str(alert_config["signal"]),
        observed=observed,
        expected_max=float(alert_config["expected_max"]),
        action=str(alert_config["action"]),
        created_at=by_type["ALERT_CREATED"].occurred_at,
        synthetic=bool(incident_config["synthetic"]),
        routing_mode=str(alert_config["routing"]["mode"]),
        live_paging=bool(alert_config["routing"]["live_paging"]),
    )
