"""Persistence helpers for Phase 3 drift evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .models import DriftReport


def save_reference_profile(frame: pd.DataFrame, features: list[str], path: str | Path) -> Path:
    profile: dict[str, Any] = {"row_count": len(frame), "features": {}}
    for feature in features:
        series = pd.to_numeric(frame[feature], errors="coerce")
        clean = series.dropna()
        profile["features"][feature] = {
            "mean": None if clean.empty else float(clean.mean()),
            "std": None if clean.empty else float(clean.std()),
            "min": None if clean.empty else float(clean.min()),
            "max": None if clean.empty else float(clean.max()),
            "null_rate": float(series.isna().mean()),
        }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile, indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_drift_report(report: DriftReport, json_path: str | Path, csv_path: str | Path) -> tuple[Path, Path]:
    json_output = Path(json_path)
    csv_output = Path(csv_path)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    rows = [result.to_dict() for result in report.feature_results]
    if report.prediction_result is not None:
        rows.append(report.prediction_result.to_dict())
    pd.DataFrame(rows).to_csv(csv_output, index=False)
    return json_output, csv_output
