from __future__ import annotations

from datetime import UTC, datetime

import pytest

from creditscore.incident_ops import IncidentEvent, elapsed_minutes, evaluate_slas


def _event(event_type: str, minute: int) -> IncidentEvent:
    return IncidentEvent(
        event_id=event_type,
        incident_id="INC",
        event_type=event_type,
        occurred_at=datetime(2026, 1, 1, minute // 60, minute % 60, tzinfo=UTC),
        source="test",
        description=event_type,
    )


def test_elapsed_minutes_is_exact() -> None:
    assert elapsed_minutes(_event("START", 0), _event("END", 184)) == 184


def test_evaluate_slas_passes_at_or_below_target() -> None:
    metrics = evaluate_slas(
        [_event("START", 0), _event("END", 184)],
        [{"name": "detect", "start_event": "START", "end_event": "END", "target_minutes": 240}],
    )
    assert metrics[0].observed_minutes == 184
    assert metrics[0].status == "PASS"


def test_evaluate_slas_fails_over_target() -> None:
    metrics = evaluate_slas(
        [_event("START", 0), _event("END", 184)],
        [{"name": "detect", "start_event": "START", "end_event": "END", "target_minutes": 100}],
    )
    assert metrics[0].status == "FAIL"


def test_evaluate_slas_rejects_missing_event() -> None:
    with pytest.raises(ValueError, match="missing events"):
        evaluate_slas(
            [_event("START", 0)],
            [{"name": "detect", "start_event": "START", "end_event": "END", "target_minutes": 240}],
        )
