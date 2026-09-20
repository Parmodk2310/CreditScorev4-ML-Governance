from __future__ import annotations

from creditscore.incident_ops import build_alert_record, build_timeline


def _config() -> dict:
    return {
        "incident": {"incident_id": "INC-1", "synthetic": True},
        "timeline": {
            "events": [
                {
                    "event_id": "1",
                    "event_type": "INCIDENT_DETECTED",
                    "occurred_at": "2026-01-01T03:04:00+00:00",
                    "source": "phase2",
                    "description": "detected",
                },
                {
                    "event_id": "2",
                    "event_type": "ALERT_CREATED",
                    "occurred_at": "2026-01-01T03:05:00+00:00",
                    "source": "phase13",
                    "description": "alert",
                },
            ]
        },
        "alert": {
            "alert_id": "ALERT-1",
            "severity": "HIGH",
            "status": "OPEN",
            "source": "phase2_data_quality",
            "signal": "device_risk_score_null_rate",
            "expected_max": 0.05,
            "action": "BLOCK_AND_QUARANTINE",
            "routing": {"mode": "evidence_only", "live_paging": False},
        },
    }


def test_alert_uses_phase2_observed_missingness() -> None:
    config = _config()
    record = build_alert_record(
        config=config,
        events=build_timeline(config),
        phase2_summary={"incident": {"device_risk_null_rate": 0.22}},
    )
    assert record.observed == 0.22
    assert record.action == "BLOCK_AND_QUARANTINE"


def test_alert_is_synthetic_and_has_no_live_paging() -> None:
    config = _config()
    record = build_alert_record(
        config=config,
        events=build_timeline(config),
        phase2_summary={"incident": {"device_risk_null_rate": 0.22}},
    )
    assert record.synthetic is True
    assert record.live_paging is False
    assert record.routing_mode == "evidence_only"
