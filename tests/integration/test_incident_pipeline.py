from creditscore.data.generator import SyntheticDataConfig, generate_lending_dataset
from creditscore.data.loader import split_train_holdout
from creditscore.incidents.vendor_migration import VendorMigrationConfig, VendorMigrationIncident
from creditscore.model.evaluate import evaluate_model
from creditscore.model.train import train_model


def test_vendor_migration_materially_degrades_same_model():
    frame = generate_lending_dataset(SyntheticDataConfig(n_samples=18_000, random_seed=42))
    train, holdout = split_train_holdout(frame, test_size=0.30, random_state=42)
    model = train_model(
        train,
        target_column="default_30d",
        model_params={
            "n_estimators": 180,
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "min_child_weight": 4,
            "reg_lambda": 2.0,
            "eval_metric": "logloss",
            "n_jobs": 2,
            "random_state": 42,
        },
    )
    baseline, _ = evaluate_model(model, holdout, scenario="baseline", vendor="vendor_a")
    migrated = VendorMigrationIncident(VendorMigrationConfig(random_seed=43)).apply(holdout)
    incident, _ = evaluate_model(model, migrated, scenario="incident", vendor="vendor_b")

    assert baseline["roc_auc"] >= 0.76
    assert baseline["roc_auc"] - incident["roc_auc"] >= 0.035
    assert 0.20 <= incident["device_risk_null_rate"] <= 0.24
