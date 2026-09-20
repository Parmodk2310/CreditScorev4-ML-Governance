"""Incident SLA evaluation for deterministic Phase 13 evidence."""

from __future__ import annotations

from typing import Any

from .models import IncidentEvent, SLAMetric
from .timeline import event_map


def elapsed_minutes(start: IncidentEvent, end: IncidentEvent) -> int:
    seconds = (end.occurred_at - start.occurred_at).total_seconds()
    if seconds < 0:
        raise ValueError(f"Event {end.event_type} occurs before {start.event_type}")
    if seconds % 60 != 0:
        raise ValueError("Phase 13 deterministic SLA fixture requires minute-aligned timestamps")
    return int(seconds // 60)


def evaluate_slas(
    events: list[IncidentEvent],
    metric_config: list[dict[str, Any]],
) -> list[SLAMetric]:
    by_type = event_map(events)
    metrics: list[SLAMetric] = []

    for payload in metric_config:
        start_type = str(payload["start_event"])
        end_type = str(payload["end_event"])
        if start_type not in by_type or end_type not in by_type:
            raise ValueError(f"SLA references missing events: {start_type} -> {end_type}")

        observed = elapsed_minutes(by_type[start_type], by_type[end_type])
        target = int(payload["target_minutes"])
        metrics.append(
            SLAMetric(
                name=str(payload["name"]),
                start_event=start_type,
                end_event=end_type,
                observed_minutes=observed,
                target_minutes=target,
                status="PASS" if observed <= target else "FAIL",
            )
        )

    return metrics
