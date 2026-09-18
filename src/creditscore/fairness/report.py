"""Fairness evidence persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .models import FairnessReport


def save_fairness_report(
    report: FairnessReport,
    json_path: str | Path,
    csv_path: str | Path,
) -> tuple[Path, Path]:
    json_path = Path(json_path)
    csv_path = Path(csv_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    rows: list[dict] = []
    for dataset_name, assessments in (("reference", report.reference), ("current", report.current)):
        for assessment in assessments:
            for group_metric in assessment.group_metrics:
                row = group_metric.to_dict()
                row.update(
                    {
                        "dataset": dataset_name,
                        "assessment_status": assessment.status,
                        "demographic_parity_ratio": assessment.demographic_parity_ratio,
                        "demographic_parity_difference": assessment.demographic_parity_difference,
                        "equalized_odds_difference": assessment.equalized_odds_difference,
                    }
                )
                rows.append(row)
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return json_path, csv_path
