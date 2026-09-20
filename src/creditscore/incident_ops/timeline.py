"""Deterministic incident timeline helpers for Phase 13."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import IncidentEvent


def parse_timestamp(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"Timestamp must be timezone-aware: {value}")
    return timestamp


def build_timeline(config: dict[str, Any]) -> list[IncidentEvent]:
    incident_id = str(config["incident"]["incident_id"])
    events: list[IncidentEvent] = []

    for payload in config["timeline"]["events"]:
        events.append(
            IncidentEvent(
                event_id=str(payload["event_id"]),
                incident_id=incident_id,
                event_type=str(payload["event_type"]),
                occurred_at=parse_timestamp(str(payload["occurred_at"])),
                source=str(payload["source"]),
                description=str(payload["description"]),
                evidence_path=(
                    str(payload["evidence_path"]) if payload.get("evidence_path") is not None else None
                ),
            )
        )

    validate_timeline(events)
    return events


def validate_timeline(events: list[IncidentEvent]) -> None:
    if not events:
        raise ValueError("Phase 13 requires at least one incident event")

    event_ids = [event.event_id for event in events]
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("Incident event ids must be unique")

    event_types = [event.event_type for event in events]
    if len(event_types) != len(set(event_types)):
        raise ValueError("Incident event types must be unique for this deterministic fixture")

    incident_ids = {event.incident_id for event in events}
    if len(incident_ids) != 1:
        raise ValueError("All incident events must share one incident id")

    if any(event.occurred_at.tzinfo is None or event.occurred_at.utcoffset() is None for event in events):
        raise ValueError("All incident timestamps must be timezone-aware")

    timestamps = [event.occurred_at for event in events]
    if timestamps != sorted(timestamps):
        raise ValueError("Incident timeline must be chronologically sorted")


def event_map(events: list[IncidentEvent]) -> dict[str, IncidentEvent]:
    return {event.event_type: event for event in events}


def required_event_types_present(
    events: list[IncidentEvent],
    required: set[str],
) -> bool:
    return required <= {event.event_type for event in events}
