from __future__ import annotations

from creditscore.business_impact import (
    compare_business_impact,
    evaluate_scenario,
)
from creditscore.data.generator import (
    SyntheticDataConfig,
    generate_lending_dataset,
)
from creditscore.data.loader import split_train_holdout
from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.incidents.vendor_migration import (
    VendorMigrationConfig,
    VendorMigrationIncident,
)
from creditscore.model.train import train_model


def test_vendor_migration_changes_approval_cohort_business_risk() -> None:
    frame = generate_lending_dataset(
        SyntheticDataConfig(
            n_samples=18_000,
            random_seed=42,
            baseline_device_null_rate=0.03,
        )
    )
    train, healthy = split_train_holdout(
        frame,
        test_size=0.30,
        random_state=42,
    )

    model = train_model(
        train,
        target_column="default_30d",
        model_params={
            "n_estimators": 280,
            "max_depth": 4,
            "learning_rate": 0.04,
            "subsample": 0.90,
            "colsample_bytree": 0.90,
            "min_child_weight": 4,
            "reg_lambda": 2.0,
            "eval_metric": "logloss",
            "n_jobs": 4,
            "random_state": 42,
        },
    )

    incident = VendorMigrationIncident(VendorMigrationConfig(random_seed=43)).apply(healthy)

    healthy_risk = model.predict_proba(healthy[MODEL_INPUT_FEATURES].copy())[:, 1]
    incident_risk = model.predict_proba(incident[MODEL_INPUT_FEATURES].copy())[:, 1]

    healthy_metrics = evaluate_scenario(
        healthy,
        healthy_risk,
        scenario="healthy",
    )
    incident_metrics = evaluate_scenario(
        incident,
        incident_risk,
        scenario="incident",
    )
    comparison = compare_business_impact(
        healthy,
        incident,
        healthy_risk,
        incident_risk,
    )

    assert comparison.same_population is True
    assert comparison.same_labels is True
    assert incident_metrics.device_risk_null_rate >= 0.20
    assert incident_metrics.approval_rate > healthy_metrics.approval_rate
    assert incident_metrics.approved_default_rate > healthy_metrics.approved_default_rate
    assert comparison.newly_approved_count > 0
