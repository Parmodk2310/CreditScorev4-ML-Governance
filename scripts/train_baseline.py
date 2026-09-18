#!/usr/bin/env python3
"""Train and evaluate the healthy Vendor A CreditScoreV4 baseline."""
from __future__ import annotations

import argparse

from creditscore.data.loader import load_csv
from creditscore.model.evaluate import evaluate_model, save_metrics, save_roc_plot
from creditscore.model.train import save_model, train_model
from creditscore.utils.config import load_config, project_root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    cfg = load_config(args.config)
    root = project_root()

    train_df = load_csv(root / "data/raw/vendor_a/train.csv")
    holdout_df = load_csv(root / "data/raw/vendor_a/holdout.csv")
    model = train_model(
        train_df,
        target_column=cfg["data"]["target_column"],
        model_params=cfg["model"]["params"],
    )
    model_path = save_model(model, root / "models/baseline/creditscorev4.joblib")
    metrics, _ = evaluate_model(
        model,
        holdout_df,
        target_column=cfg["data"]["target_column"],
        threshold=float(cfg["model"]["decision_threshold"]),
        scenario="baseline",
        vendor="vendor_a",
    )
    save_metrics(metrics, root / "data/evidence/phase1/baseline_metrics.json")
    save_roc_plot(model, holdout_df, root / "data/evidence/phase1/baseline_roc.png", title="CreditScoreV4 — Healthy Vendor A")

    print(f"Saved model: {model_path}")
    print(f"Baseline ROC-AUC={metrics['roc_auc']:.4f}")
    print(f"Baseline device_risk_score NULL rate={metrics['device_risk_null_rate']:.3%}")


if __name__ == "__main__":
    main()
