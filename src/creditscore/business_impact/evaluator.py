"""Evaluate lending decision impact under a controlled vendor migration."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .models import BusinessImpactComparison, BusinessImpactMetrics


def _as_probabilities(
    values: Sequence[float] | np.ndarray,
    expected: int,
) -> np.ndarray:
    probabilities = np.asarray(values, dtype=float)

    if probabilities.ndim != 1:
        raise ValueError("Probabilities must be one-dimensional.")
    if len(probabilities) != expected:
        raise ValueError("Probability count does not match frame length.")
    if not np.isfinite(probabilities).all():
        raise ValueError("Probabilities must be finite.")
    if ((probabilities < 0.0) | (probabilities > 1.0)).any():
        raise ValueError("Probabilities must be in [0, 1].")

    return probabilities


def _require_columns(frame: pd.DataFrame, target_column: str) -> None:
    required = {"application_id", target_column, "device_risk_score"}
    missing = required.difference(frame.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def evaluate_scenario(
    frame: pd.DataFrame,
    probabilities: Sequence[float] | np.ndarray,
    *,
    scenario: str,
    threshold: float = 0.50,
    target_column: str = "default_30d",
) -> BusinessImpactMetrics:
    """Calculate decision and observed-outcome metrics for one scenario."""

    _require_columns(frame, target_column)

    if not 0.0 < threshold < 1.0:
        raise ValueError("Approval threshold must be between 0 and 1.")

    risk = _as_probabilities(probabilities, len(frame))
    target = frame[target_column].astype(int).to_numpy()

    approved = risk < threshold
    approval_count = int(approved.sum())

    if approval_count == 0:
        raise ValueError("Scenario produced no approved applicants.")

    device = pd.to_numeric(frame["device_risk_score"], errors="coerce")

    return BusinessImpactMetrics(
        scenario=scenario,
        sample_count=len(frame),
        approval_count=approval_count,
        approval_rate=float(approved.mean()),
        overall_default_rate=float(target.mean()),
        approved_default_rate=float(target[approved].mean()),
        mean_predicted_risk=float(risk.mean()),
        approved_mean_predicted_risk=float(risk[approved].mean()),
        device_risk_null_rate=float(device.isna().mean()),
        device_risk_observed_mean=float(device.mean()),
    )


def compare_business_impact(
    healthy: pd.DataFrame,
    incident: pd.DataFrame,
    healthy_probabilities: Sequence[float] | np.ndarray,
    incident_probabilities: Sequence[float] | np.ndarray,
    *,
    threshold: float = 0.50,
    target_column: str = "default_30d",
) -> BusinessImpactComparison:
    """Compare decisions on the same applicant population and outcome labels."""

    _require_columns(healthy, target_column)
    _require_columns(incident, target_column)

    healthy_ids = healthy["application_id"].astype(str).to_numpy()
    incident_ids = incident["application_id"].astype(str).to_numpy()

    same_population = len(healthy) == len(incident) and np.array_equal(
        healthy_ids,
        incident_ids,
    )
    if not same_population:
        raise ValueError("Healthy and incident frames must contain the same ordered population.")

    healthy_target = healthy[target_column].astype(int).to_numpy()
    incident_target = incident[target_column].astype(int).to_numpy()

    same_labels = np.array_equal(healthy_target, incident_target)
    if not same_labels:
        raise ValueError("Healthy and incident frames must preserve the same outcome labels.")

    healthy_risk = _as_probabilities(healthy_probabilities, len(healthy))
    incident_risk = _as_probabilities(incident_probabilities, len(incident))

    healthy_metrics = evaluate_scenario(
        healthy,
        healthy_risk,
        scenario="healthy_vendor_a",
        threshold=threshold,
        target_column=target_column,
    )
    incident_metrics = evaluate_scenario(
        incident,
        incident_risk,
        scenario="vendor_b_incident",
        threshold=threshold,
        target_column=target_column,
    )

    healthy_approved = healthy_risk < threshold
    incident_approved = incident_risk < threshold

    newly_approved = (~healthy_approved) & incident_approved
    newly_rejected = healthy_approved & (~incident_approved)
    flipped = healthy_approved != incident_approved

    newly_approved_default_rate: float | None
    if newly_approved.any():
        newly_approved_default_rate = float(healthy_target[newly_approved].mean())
    else:
        newly_approved_default_rate = None

    return BusinessImpactComparison(
        same_population=True,
        same_labels=True,
        approval_rate_change=(incident_metrics.approval_rate - healthy_metrics.approval_rate),
        approved_default_rate_change=(
            incident_metrics.approved_default_rate - healthy_metrics.approved_default_rate
        ),
        overall_default_rate_change=(
            incident_metrics.overall_default_rate - healthy_metrics.overall_default_rate
        ),
        mean_predicted_risk_change=(
            incident_metrics.mean_predicted_risk - healthy_metrics.mean_predicted_risk
        ),
        device_null_rate_change=(
            incident_metrics.device_risk_null_rate - healthy_metrics.device_risk_null_rate
        ),
        device_observed_mean_change=(
            incident_metrics.device_risk_observed_mean - healthy_metrics.device_risk_observed_mean
        ),
        newly_approved_count=int(newly_approved.sum()),
        newly_rejected_count=int(newly_rejected.sum()),
        decision_flip_count=int(flipped.sum()),
        decision_flip_rate=float(flipped.mean()),
        newly_approved_default_rate=newly_approved_default_rate,
    )
