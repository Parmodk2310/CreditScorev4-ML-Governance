"""Generate Phase 9 business-impact evidence from the verified Vendor A/B incident."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from creditscore.business_impact import compare_business_impact, evaluate_scenario
from creditscore.data.loader import load_csv
from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.model.train import load_model
from creditscore.utils.config import decision_settings, load_yaml, project_root
from creditscore.utils.hashing import file_sha256


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    root = project_root()
    config = load_yaml(root / "configs" / "phase9.yaml")

    target_column, threshold = decision_settings(root)

    healthy_path = root / "data/raw/vendor_a/holdout.csv"
    incident_path = root / "data/raw/vendor_b/holdout.csv"
    model_path = root / "models/baseline/creditscorev4.joblib"

    for path in (healthy_path, incident_path, model_path):
        if not path.exists():
            raise FileNotFoundError(
                f"Required Phase 1 artifact is missing: {path}. " "Run make phase1-verify first."
            )

    healthy = load_csv(healthy_path)
    incident = load_csv(incident_path)
    model = load_model(model_path)

    healthy_probabilities = model.predict_proba(healthy[MODEL_INPUT_FEATURES].copy())[:, 1]
    incident_probabilities = model.predict_proba(incident[MODEL_INPUT_FEATURES].copy())[:, 1]

    healthy_metrics = evaluate_scenario(
        healthy,
        healthy_probabilities,
        scenario="healthy_vendor_a",
        threshold=threshold,
        target_column=target_column,
    )
    incident_metrics = evaluate_scenario(
        incident,
        incident_probabilities,
        scenario="vendor_b_incident",
        threshold=threshold,
        target_column=target_column,
    )
    comparison = compare_business_impact(
        healthy,
        incident,
        healthy_probabilities,
        incident_probabilities,
        threshold=threshold,
        target_column=target_column,
    )

    report = {
        "schema_version": 1,
        "phase": 9,
        "name": "business-impact-incident-evidence",
        "decision_threshold": threshold,
        "target_column": target_column,
        "healthy": healthy_metrics.to_dict(),
        "incident": incident_metrics.to_dict(),
        "comparison": comparison.to_dict(),
        "traceability": {
            "healthy_holdout_sha256": file_sha256(healthy_path),
            "incident_holdout_sha256": file_sha256(incident_path),
            "model_artifact_sha256": file_sha256(model_path),
        },
    }

    report_path = root / str(config["evidence"]["report"])
    _write_json(report, report_path)

    cohort_summary = pd.DataFrame(
        [
            healthy_metrics.to_dict(),
            incident_metrics.to_dict(),
        ]
    )
    cohort_path = root / str(config["evidence"]["cohort_summary"])
    cohort_path.parent.mkdir(parents=True, exist_ok=True)
    cohort_summary.to_csv(cohort_path, index=False)

    transition_path = root / str(config["evidence"]["transition_summary"])
    _write_json(
        {
            "same_population": comparison.same_population,
            "same_labels": comparison.same_labels,
            "newly_approved_count": comparison.newly_approved_count,
            "newly_rejected_count": comparison.newly_rejected_count,
            "decision_flip_count": comparison.decision_flip_count,
            "decision_flip_rate": comparison.decision_flip_rate,
            "newly_approved_default_rate": (comparison.newly_approved_default_rate),
        },
        transition_path,
    )

    print("CreditScoreV4 — Phase 9 Business Impact")
    print("=" * 43)
    print(f"Healthy approval rate........... " f"{healthy_metrics.approval_rate:.2%}")
    print(f"Incident approval rate.......... " f"{incident_metrics.approval_rate:.2%}")
    print(f"Approval-rate change............ " f"{comparison.approval_rate_change:+.2%}")
    print("Healthy approved default rate.. " f"{healthy_metrics.approved_default_rate:.2%}")
    print("Incident approved default rate. " f"{incident_metrics.approved_default_rate:.2%}")
    print("Approved-default change........ " f"{comparison.approved_default_rate_change:+.2%}")
    print("Mean predicted-risk change..... " f"{comparison.mean_predicted_risk_change:+.4f}")
    print("Device NULL-rate change........ " f"{comparison.device_null_rate_change:+.2%}")
    print(f"Newly approved applicants....... " f"{comparison.newly_approved_count}")
    print(f"Newly rejected applicants....... " f"{comparison.newly_rejected_count}")
    print(f"Decision flips.................. " f"{comparison.decision_flip_count}")
    print(f"Decision flip rate............... " f"{comparison.decision_flip_rate:.2%}")

    if comparison.newly_approved_default_rate is not None:
        print("Newly-approved default rate.... " f"{comparison.newly_approved_default_rate:.2%}")

    print(f"\nEvidence report................. " f"{report_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
