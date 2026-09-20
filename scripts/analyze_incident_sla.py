#!/usr/bin/env python3
"""Generate Phase 13 deterministic incident-SLA and alert evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from creditscore.incident_ops import build_phase13_evidence
from creditscore.utils.config import load_yaml, project_root
from creditscore.utils.hashing import file_sha256


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    root = project_root()
    config = load_yaml(root / "configs" / "phase13.yaml")
    evidence = config["evidence"]

    contract_path = root / str(evidence["data_contract"])
    phase2_path = root / str(evidence["phase2_summary"])
    phase9_path = root / str(evidence["phase9_report"])
    phase10_path = root / str(evidence["phase10_report"])

    required = (contract_path, phase2_path, phase9_path, phase10_path)
    missing = [path for path in required if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing Phase 13 prerequisite: {path.relative_to(root)}")
        return 1

    phase2 = _read_json(phase2_path)
    phase9 = _read_json(phase9_path)
    phase10 = _read_json(phase10_path)

    traceability = {
        "data_contract_sha256": file_sha256(contract_path),
        "phase2_summary_sha256": file_sha256(phase2_path),
        "phase9_report_sha256": file_sha256(phase9_path),
        "phase10_report_sha256": file_sha256(phase10_path),
    }

    result = build_phase13_evidence(
        config=config,
        phase2_summary=phase2,
        phase9_report=phase9,
        phase10_report=phase10,
        traceability=traceability,
    )

    timeline_path = root / str(evidence["timeline"])
    events_path = root / str(evidence["events"])
    alert_path = root / str(evidence["alert"])
    sla_path = root / str(evidence["sla_summary"])
    report_path = root / str(evidence["incident_report"])

    _write_json(timeline_path, result["timeline"])
    _write_json(alert_path, result["alert"])
    _write_json(sla_path, result["sla"])
    _write_json(report_path, result["report"])

    events_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.write_text(
        "".join(json.dumps(event.to_dict(), sort_keys=True) + "\n" for event in result["events"]),
        encoding="utf-8",
    )

    metrics = {item["name"]: item for item in result["sla"]["metrics"]}

    print("CreditScoreV4 — Phase 13 Incident SLA & Alerting")
    print("=" * 51)
    print(f"Incident id....................... {config['incident']['incident_id']}")
    print(f"Vendor B Phase 2 decision......... {phase2['incident']['decision']}")
    print(f"Alert severity.................... {result['alert']['severity']}")
    print(f"Live paging....................... {str(result['alert']['routing']['live_paging']).lower()}")
    print()
    print(f"Detection latency................. {metrics['time_to_detect']['observed_minutes']} min")
    print(f"Alert latency..................... {metrics['time_to_alert']['observed_minutes']} min")
    print(f"Governance block latency.......... {metrics['time_to_block']['observed_minutes']} min")
    print(f"Triage latency.................... {metrics['time_to_triage']['observed_minutes']} min")
    print(f"Root-cause completion............. {metrics['time_to_root_cause']['observed_minutes']} min")
    print(f"Root-cause SLA target............. <= {metrics['time_to_root_cause']['target_minutes']} min")
    print(f"Root-cause SLA status............. {metrics['time_to_root_cause']['status']}")
    print()
    print(f"Incident report................... {report_path.relative_to(root)}")
    print(
        "NOTE: all timestamps and SLAs are deterministic synthetic operational evidence; "
        "no live paging or production MTTR is claimed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
