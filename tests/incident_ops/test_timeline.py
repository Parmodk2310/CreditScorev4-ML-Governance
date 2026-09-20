from __future__ import annotations

from datetime import UTC, datetime

import pytest

from creditscore.incident_ops import IncidentEvent, build_timeline, parse_timestamp, validate_timeline


def _config() -> dict:
    return {
        "incident": {"incident_id": "INC-1"},
        "timeline": {
            "events": [
                {
                    "event_id": "1",
                    "event_type": "START",
                    "occurred_at": "2026-01-01T00:00:00+00:00",
                    "source": "test",
                    "description": "start",
                },
                {
                    "event_id": "2",
                    "event_type": "END",
                    "occurred_at": "2026-01-01T01:00:00+00:00",
                    "source": "test",
                    "description": "end",
                },
            ]
        },
    }


def test_parse_timestamp_requires_timezone() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_timestamp("2026-01-01T00:00:00")


def test_build_timeline_preserves_order_and_incident_id() -> None:
    events = build_timeline(_config())
    assert [event.event_type for event in events] == ["START", "END"]
    assert {event.incident_id for event in events} == {"INC-1"}


def test_validate_timeline_rejects_out_of_order_events() -> None:
    events = [
        IncidentEvent("1", "INC", "A", datetime(2026, 1, 1, 1, tzinfo=UTC), "x", "a"),
        IncidentEvent("2", "INC", "B", datetime(2026, 1, 1, 0, tzinfo=UTC), "x", "b"),
    ]
    with pytest.raises(ValueError, match="chronologically sorted"):
        validate_timeline(events)


def test_validate_timeline_rejects_duplicate_event_types() -> None:
    events = [
        IncidentEvent("1", "INC", "A", datetime(2026, 1, 1, 0, tzinfo=UTC), "x", "a"),
        IncidentEvent("2", "INC", "A", datetime(2026, 1, 1, 1, tzinfo=UTC), "x", "b"),
    ]
    with pytest.raises(ValueError, match="event types"):
        validate_timeline(events)
