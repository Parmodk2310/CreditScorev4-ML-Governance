"""Data models for Phase 13 incident operations evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class IncidentEvent:
    event_id: str
    incident_id: str
    event_type: str
    occurred_at: datetime
    source: str
    description: str
    evidence_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event_id": self.event_id,
            "incident_id": self.incident_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "source": self.source,
            "description": self.description,
        }
        if self.evidence_path is not None:
            payload["evidence_path"] = self.evidence_path
        return payload


@dataclass(frozen=True)
class SLAMetric:
    name: str
    start_event: str
    end_event: str
    observed_minutes: int
    target_minutes: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start_event": self.start_event,
            "end_event": self.end_event,
            "observed_minutes": self.observed_minutes,
            "target_minutes": self.target_minutes,
            "status": self.status,
        }


@dataclass(frozen=True)
class AlertRecord:
    alert_id: str
    incident_id: str
    severity: str
    status: str
    source: str
    signal: str
    observed: float
    expected_max: float
    action: str
    created_at: datetime
    synthetic: bool
    routing_mode: str
    live_paging: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "phase": 13,
            "alert_id": self.alert_id,
            "incident_id": self.incident_id,
            "severity": self.severity,
            "status": self.status,
            "source": self.source,
            "signal": self.signal,
            "observed": self.observed,
            "expected_max": self.expected_max,
            "action": self.action,
            "created_at": self.created_at.isoformat(),
            "synthetic": self.synthetic,
            "routing": {
                "mode": self.routing_mode,
                "live_paging": self.live_paging,
            },
        }
