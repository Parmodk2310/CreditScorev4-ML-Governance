"""Apply Vendor B migration to the healthy holdout and evaluate the same model."""

from __future__ import annotations

import argparse
import json

import pandas as pd

from creditscore.data.loader import load_csv
from creditscore.incidents.vendor_migration import VendorMigrationConfig, VendorMigrationIncident
from creditscore.model.evaluate import evaluate_model, save_metrics, save_roc_plot
from creditscore.model.train import load_model
from creditscore.utils.config import decision_target_column, decision_threshold, load_config, project_root
from creditscore.utils.hashing import file_sha256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    cfg = load_config(args.config)
    root = project_root()

    healthy = load_csv(root / "data/raw/vendor_a/holdout.csv")
    incident_cfg = VendorMigrationConfig(
        target_device_null_rate=float(cfg["incident"]["target_device_null_rate"]),
        semantic_attenuation=float(cfg["incident"]["semantic_attenuation"]),
        semantic_bias=float(cfg["incident"]["semantic_bias"]),
        semantic_noise_std=float(cfg["incident"]["semantic_noise_std"]),
        random_seed=int(cfg["project"]["random_seed"]) + 1,
    )
    migrated = VendorMigrationIncident(incident_cfg).apply(healthy)
    vendor_b_path = root / "data/raw/vendor_b/holdout.csv"
    vendor_b_path.parent.mkdir(parents=True, exist_ok=True)
    migrated.to_csv(vendor_b_path, index=False)

    model = load_model(root / "models/baseline/creditscorev4.joblib")
    metrics, _ = evaluate_model(
        model,
        migrated,
        target_column=decision_target_column(root),
        threshold=decision_threshold(root),
        scenario="vendor_migration_incident",
        vendor="vendor_b",
    )
    save_metrics(metrics, root / "data/evidence/phase1/incident_metrics.json")
    save_roc_plot(
        model,
        migrated,
        root / "data/evidence/phase1/incident_roc.png",
        title="CreditScoreV4 — Vendor B Incident",
    )

    baseline_metrics = json.loads(
        (root / "data/evidence/phase1/baseline_metrics.json").read_text(encoding="utf-8")
    )
    comparison = {
        "baseline_roc_auc": baseline_metrics["roc_auc"],
        "incident_roc_auc": metrics["roc_auc"],
        "auc_drop": baseline_metrics["roc_auc"] - metrics["roc_auc"],
        "baseline_device_risk_null_rate": baseline_metrics["device_risk_null_rate"],
        "incident_device_risk_null_rate": metrics["device_risk_null_rate"],
        "vendor_b_file_sha256": file_sha256(vendor_b_path),
    }
    (root / "data/evidence/phase1/performance_comparison.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True), encoding="utf-8"
    )

    missingness = pd.DataFrame(
        {
            "scenario": ["vendor_a_healthy", "vendor_b_incident"],
            "device_risk_null_rate": [
                healthy["device_risk_score"].isna().mean(),
                migrated["device_risk_score"].isna().mean(),
            ],
        }
    )
    missingness.to_csv(root / "data/evidence/phase1/missingness_comparison.csv", index=False)

    print(f"Incident ROC-AUC={metrics['roc_auc']:.4f}")
    print(f"Incident device_risk_score NULL rate={metrics['device_risk_null_rate']:.3%}")
    print(f"AUC drop={comparison['auc_drop']:.4f}")


if __name__ == "__main__":
    main()
