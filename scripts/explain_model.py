#!/usr/bin/env python3
"""Generate global, subgroup, and local SHAP evidence for Phase 4."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from creditscore.explainability import ShapEngine
from creditscore.model.train import load_model
from creditscore.utils.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def run_explainability():
    config = load_yaml(ROOT / "configs" / "phase4.yaml")
    current = pd.read_csv(ROOT / config["scenario"]["output"])
    model = load_model(ROOT / config["paths"]["model"])
    explain = config["explainability"]

    engine = ShapEngine(model)
    analysis = engine.explain(
        current,
        sensitive_feature=str(config["fairness"]["primary_sensitive_feature"]),
        primary_group=str(explain["primary_group"]),
        sample_size=int(explain["sample_size"]),
        random_seed=int(explain["random_seed"]),
        top_k=int(explain["top_k"]),
        local_examples=int(explain["local_examples"]),
    )
    engine.save(
        analysis,
        summary_path=ROOT / config["paths"]["shap_summary_json"],
        global_path=ROOT / config["paths"]["shap_global_csv"],
        group_path=ROOT / config["paths"]["shap_group_csv"],
        delta_path=ROOT / config["paths"]["shap_delta_csv"],
    )
    return analysis


def main() -> None:
    analysis = run_explainability()
    print("CreditScoreV4 — Phase 4 SHAP Explainability")
    print("=" * 45)
    print(f"Sample size......................... {analysis.summary['sample_size']:,}")
    print(f"Primary group....................... {analysis.summary['primary_group']}")
    print("Protected attributes in model....... NONE")
    print()
    print("Top global features")
    for row in analysis.global_importance.head(10).itertuples(index=False):
        print(f"  {int(row.rank):2d}. {row.feature:40} mean|SHAP|={row.mean_abs_shap:.4f}")
    print()
    print("Top positive primary-group features")
    for feature in analysis.summary["top_positive_primary_group_features"]:
        print(f"  - {feature}")


if __name__ == "__main__":
    main()
