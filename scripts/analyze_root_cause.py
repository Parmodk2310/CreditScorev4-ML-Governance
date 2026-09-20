#!/usr/bin/env python3
"""Generate Phase 10 root-cause ablation and remediation evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from creditscore.business_impact import evaluate_scenario
from creditscore.data.loader import load_csv
from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.incidents.vendor_migration import (
    VendorMigrationConfig,
)
from creditscore.model.metrics import calculate_classification_metrics
from creditscore.model.train import load_model
from creditscore.root_cause import (
    RootCauseScenarioMetrics,
    build_ablation_frames,
    factorial_effect,
    fitted_device_median,
    predict_with_device_value_override,
)
from creditscore.utils.config import load_config, load_yaml, project_root
from creditscore.utils.hashing import file_sha256


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _frames_equivalent(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    if list(left.columns) != list(right.columns) or len(left) != len(right):
        return False

    for column in left.columns:
        if pd.api.types.is_numeric_dtype(left[column]):
            left_values = pd.to_numeric(
                left[column],
                errors="coerce",
            ).to_numpy()
            right_values = pd.to_numeric(
                right[column],
                errors="coerce",
            ).to_numpy()
            if not np.allclose(
                left_values,
                right_values,
                equal_nan=True,
                rtol=1e-12,
                atol=1e-12,
            ):
                return False
        elif not left[column].astype(str).equals(right[column].astype(str)):
            return False

    return True


def _scenario_metrics(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    *,
    scenario: str,
    target_column: str,
    threshold: float,
    healthy_probabilities: np.ndarray,
) -> RootCauseScenarioMetrics:
    business = evaluate_scenario(
        frame,
        probabilities,
        scenario=scenario,
        threshold=threshold,
        target_column=target_column,
    )
    quality = calculate_classification_metrics(
        frame[target_column].astype(int),
        probabilities,
        threshold=threshold,
    )

    healthy_approved = healthy_probabilities < threshold
    scenario_approved = probabilities < threshold
    flipped = healthy_approved != scenario_approved
    newly_approved = (~healthy_approved) & scenario_approved
    newly_rejected = healthy_approved & (~scenario_approved)

    return RootCauseScenarioMetrics(
        scenario=scenario,
        sample_count=len(frame),
        roc_auc=float(quality["roc_auc"]),
        pr_auc=float(quality["pr_auc"]),
        brier_score=float(quality["brier_score"]),
        approval_rate=business.approval_rate,
        approved_default_rate=business.approved_default_rate,
        mean_predicted_risk=business.mean_predicted_risk,
        device_risk_null_rate=business.device_risk_null_rate,
        decision_flip_count_vs_healthy=int(flipped.sum()),
        decision_flip_rate_vs_healthy=float(flipped.mean()),
        newly_approved_count_vs_healthy=int(newly_approved.sum()),
        newly_rejected_count_vs_healthy=int(newly_rejected.sum()),
    )


def _factorial_effects(
    scenarios: dict[str, RootCauseScenarioMetrics],
) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = {}

    for metric in (
        "roc_auc",
        "pr_auc",
        "brier_score",
        "approval_rate",
        "approved_default_rate",
        "mean_predicted_risk",
    ):
        output[metric] = factorial_effect(
            float(getattr(scenarios["healthy"], metric)),
            float(getattr(scenarios["semantic_only"], metric)),
            float(getattr(scenarios["missingness_only"], metric)),
            float(getattr(scenarios["combined"], metric)),
        )

    return output


def main() -> int:
    root = project_root()
    phase10 = load_yaml(root / "configs" / "phase10.yaml")
    phase1 = load_config()

    target_column = str(phase10["decision"]["target_column"])
    threshold = float(phase10["decision"]["approval_threshold"])
    quantiles = [float(value) for value in phase10["remediation"]["training_quantiles"]]
    validation_candidate = str(phase10["remediation"]["validation_candidate"])
    validation_candidate_status = str(phase10["remediation"]["validation_candidate_status"])

    healthy_path = root / "data/raw/vendor_a/holdout.csv"
    incident_path = root / "data/raw/vendor_b/holdout.csv"
    train_path = root / "data/raw/vendor_a/train.csv"
    model_path = root / "models/baseline/creditscorev4.joblib"
    phase9_path = root / "data/evidence/phase9/business_impact.json"

    for path in (
        healthy_path,
        incident_path,
        train_path,
        model_path,
        phase9_path,
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"Required prior-phase artifact is missing: {path}. " "Run make phase9-verify first."
            )

    healthy = load_csv(healthy_path)
    stored_incident = load_csv(incident_path)
    train = load_csv(train_path)
    model = load_model(model_path)

    incident_cfg = VendorMigrationConfig(
        target_device_null_rate=float(phase1["incident"]["target_device_null_rate"]),
        semantic_attenuation=float(phase1["incident"]["semantic_attenuation"]),
        semantic_bias=float(phase1["incident"]["semantic_bias"]),
        semantic_noise_std=float(phase1["incident"]["semantic_noise_std"]),
        random_seed=int(phase1["project"]["random_seed"]) + 1,
    )

    frames = build_ablation_frames(
        healthy,
        combined_config=incident_cfg,
    )
    generated_combined_matches_vendor_b = _frames_equivalent(
        frames.combined,
        stored_incident,
    )

    frame_map = {
        "healthy": frames.healthy,
        "semantic_only": frames.semantic_only,
        "missingness_only": frames.missingness_only,
        "combined": stored_incident,
    }

    probabilities: dict[str, np.ndarray] = {}
    for name, frame in frame_map.items():
        probabilities[name] = model.predict_proba(frame[MODEL_INPUT_FEATURES].copy())[:, 1]

    healthy_probabilities = probabilities["healthy"]
    scenarios: dict[str, RootCauseScenarioMetrics] = {}

    for name, frame in frame_map.items():
        scenarios[name] = _scenario_metrics(
            frame,
            probabilities[name],
            scenario=name,
            target_column=target_column,
            threshold=threshold,
            healthy_probabilities=healthy_probabilities,
        )

    phase9_report = json.loads(phase9_path.read_text(encoding="utf-8"))
    phase9_incident = phase9_report["incident"]
    phase9_consistency = (
        abs(scenarios["combined"].approval_rate - float(phase9_incident["approval_rate"])) <= 1e-12
        and abs(scenarios["combined"].approved_default_rate - float(phase9_incident["approved_default_rate"]))
        <= 1e-12
        and abs(scenarios["combined"].mean_predicted_risk - float(phase9_incident["mean_predicted_risk"]))
        <= 1e-12
    )

    effects = _factorial_effects(scenarios)

    fitted_median = fitted_device_median(model)
    semantic_device = pd.to_numeric(
        frames.semantic_only["device_risk_score"],
        errors="coerce",
    )
    combined_device = pd.to_numeric(
        stored_incident["device_risk_score"],
        errors="coerce",
    )
    healthy_device = pd.to_numeric(
        healthy["device_risk_score"],
        errors="coerce",
    )

    newly_missing = combined_device.isna() & semantic_device.notna()
    newly_missing_count = int(newly_missing.sum())

    semantic_reference_mean = float(semantic_device.loc[newly_missing].mean())
    healthy_reference_mean = float(healthy_device.loc[newly_missing].mean())

    median_values = np.full(
        len(stored_incident),
        fitted_median,
        dtype=float,
    )
    median_control_probabilities = predict_with_device_value_override(
        model,
        stored_incident,
        median_values,
    )
    median_control_max_probability_delta = float(
        np.max(np.abs(median_control_probabilities - probabilities["combined"]))
    )

    oracle_values = np.full(
        len(stored_incident),
        fitted_median,
        dtype=float,
    )
    oracle_values[newly_missing.to_numpy()] = semantic_device.loc[newly_missing].to_numpy(dtype=float)
    oracle_probabilities = predict_with_device_value_override(
        model,
        stored_incident,
        oracle_values,
    )
    oracle_metrics = _scenario_metrics(
        stored_incident,
        oracle_probabilities,
        scenario="oracle_semantic_restore",
        target_column=target_column,
        threshold=threshold,
        healthy_probabilities=healthy_probabilities,
    )

    train_device = pd.to_numeric(
        train["device_risk_score"],
        errors="coerce",
    ).dropna()

    remediation_results: dict[str, dict[str, Any]] = {}
    remediation_rows: list[dict[str, Any]] = []

    for quantile in quantiles:
        if not 0.0 < quantile < 1.0:
            raise ValueError(f"Training quantile must be in (0, 1): {quantile}")

        value = float(train_device.quantile(quantile))
        replacement = np.full(
            len(stored_incident),
            value,
            dtype=float,
        )
        candidate_probabilities = predict_with_device_value_override(
            model,
            stored_incident,
            replacement,
        )
        candidate_name = f"training_q{round(quantile * 100)}"
        metrics = _scenario_metrics(
            stored_incident,
            candidate_probabilities,
            scenario=candidate_name,
            target_column=target_column,
            threshold=threshold,
            healthy_probabilities=healthy_probabilities,
        )

        remediation_results[candidate_name] = {
            "quantile": quantile,
            "replacement_value": value,
            "metrics": metrics.to_dict(),
            "delta_vs_current_combined": {
                "roc_auc": (metrics.roc_auc - scenarios["combined"].roc_auc),
                "approval_rate": (metrics.approval_rate - scenarios["combined"].approval_rate),
                "approved_default_rate": (
                    metrics.approved_default_rate - scenarios["combined"].approved_default_rate
                ),
                "mean_predicted_risk": (
                    metrics.mean_predicted_risk - scenarios["combined"].mean_predicted_risk
                ),
            },
        }
        remediation_rows.append(
            {
                "scenario": candidate_name,
                "quantile": quantile,
                "replacement_value": value,
                **metrics.to_dict(),
            }
        )

    report = {
        "schema_version": 1,
        "phase": 10,
        "name": "root-cause-ablation-and-remediation",
        "methodology": {
            "design": "2x2 controlled factorial ablation",
            "factor_semantic_shift": ("Vendor B score attenuation, bias, and noise"),
            "factor_elevated_missingness": ("exact Vendor B device_risk_score missingness mask"),
            "fixed_components": [
                "same applicant population",
                "same default_30d labels",
                "same trained model artifact",
                "same 0.50 decision threshold",
            ],
            "interpretation": (
                "Main effects and interaction are descriptive for this "
                "deterministic synthetic fixture. The non-linear model "
                "means effects need not be additive."
            ),
        },
        "invariants": {
            "same_population": True,
            "same_labels": True,
            "generated_combined_matches_vendor_b": (generated_combined_matches_vendor_b),
            "phase9_consistency": phase9_consistency,
        },
        "scenarios": {name: metrics.to_dict() for name, metrics in scenarios.items()},
        "factorial_effects": effects,
        "imputation_diagnostic": {
            "feature": "device_risk_score",
            "fitted_training_median": fitted_median,
            "newly_missing_count": newly_missing_count,
            "newly_missing_semantic_reference_mean": (semantic_reference_mean),
            "newly_missing_healthy_reference_mean": (healthy_reference_mean),
            "semantic_reference_minus_median": (semantic_reference_mean - fitted_median),
            "median_control_max_probability_delta": (median_control_max_probability_delta),
        },
        "counterfactuals": {
            "oracle_semantic_restore": {
                "metrics": oracle_metrics.to_dict(),
                "deployable": False,
                "reason": (
                    "Uses synthetic counterfactual values that are known "
                    "only because the healthy fixture is available."
                ),
            },
            "training_quantile_candidates": remediation_results,
        },
        "traceability": {
            "healthy_holdout_sha256": file_sha256(healthy_path),
            "incident_holdout_sha256": file_sha256(incident_path),
            "healthy_train_sha256": file_sha256(train_path),
            "model_artifact_sha256": file_sha256(model_path),
            "phase9_report_sha256": file_sha256(phase9_path),
        },
        "scope": {
            "validation_candidate": validation_candidate,
            "validation_candidate_status": validation_candidate_status,
            "candidate_selected": False,
            "production_policy_changed": False,
            "claim": (
                "Phase 10 measures mechanism contribution and fixed-model "
                "counterfactuals inside the synthetic case study. It does "
                "not establish a real-world causal or regulatory claim."
            ),
        },
    }

    report_path = root / str(phase10["evidence"]["report"])
    _write_json(report, report_path)

    scenario_path = root / str(phase10["evidence"]["scenario_summary"])
    scenario_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            scenarios[name].to_dict()
            for name in (
                "healthy",
                "semantic_only",
                "missingness_only",
                "combined",
            )
        ]
    ).to_csv(scenario_path, index=False)

    effect_rows: list[dict[str, Any]] = []
    for metric, values in effects.items():
        effect_rows.append({"metric": metric, **values})

    pd.DataFrame(effect_rows).to_csv(
        root / str(phase10["evidence"]["factorial_effects"]),
        index=False,
    )

    remediation_rows.append(
        {
            "scenario": "oracle_semantic_restore",
            "quantile": np.nan,
            "replacement_value": np.nan,
            **oracle_metrics.to_dict(),
        }
    )
    pd.DataFrame(remediation_rows).to_csv(
        root / str(phase10["evidence"]["remediation_summary"]),
        index=False,
    )

    print("CreditScoreV4 — Phase 10 Root-Cause Ablation")
    print("=" * 49)
    print(
        "Generated combined matches Vendor B... " f"{'YES' if generated_combined_matches_vendor_b else 'NO'}"
    )
    print("Phase 9 metric consistency............ " f"{'YES' if phase9_consistency else 'NO'}")

    print("\n2x2 scenario evidence")
    for name in (
        "healthy",
        "semantic_only",
        "missingness_only",
        "combined",
    ):
        metrics = scenarios[name]
        print(
            f"  {name:<17} "
            f"AUC={metrics.roc_auc:.4f}  "
            f"approval={metrics.approval_rate:.2%}  "
            f"approved_default={metrics.approved_default_rate:.2%}  "
            f"mean_risk={metrics.mean_predicted_risk:.4f}  "
            f"flips={metrics.decision_flip_count_vs_healthy}"
        )

    print("\nImputation diagnostic")
    print(f"  fitted device median................. " f"{fitted_median:.4f}")
    print(f"  newly missing rows................... " f"{newly_missing_count}")
    print("  semantic reference mean.............. " f"{semantic_reference_mean:.4f}")
    print("  semantic reference - median.......... " f"{semantic_reference_mean - fitted_median:+.4f}")
    print("  median-control max probability delta. " f"{median_control_max_probability_delta:.3e}")

    print("\nFixed-model counterfactuals")
    print(
        "  oracle semantic restore: "
        f"AUC={oracle_metrics.roc_auc:.4f}, "
        f"approval={oracle_metrics.approval_rate:.2%}, "
        f"approved_default={oracle_metrics.approved_default_rate:.2%}"
    )

    for name, payload in remediation_results.items():
        metrics = payload["metrics"]
        print(
            f"  {name}: value={payload['replacement_value']:.4f}, "
            f"AUC={metrics['roc_auc']:.4f}, "
            f"approval={metrics['approval_rate']:.2%}, "
            f"approved_default={metrics['approved_default_rate']:.2%}"
        )

    print(f"\nEvidence report......................... " f"{report_path.relative_to(root)}")
    print(
        "NOTE: Phase 10 does not select a remediation candidate yet. "
        "Review this evidence before freezing outcome gates or promoting "
        "CI to phase10-verify."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
