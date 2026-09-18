import pandas as pd

from creditscore.data.generator import SyntheticDataConfig, generate_lending_dataset


def test_generator_is_deterministic():
    cfg = SyntheticDataConfig(n_samples=500, random_seed=7, baseline_device_null_rate=0.03)
    left = generate_lending_dataset(cfg)
    right = generate_lending_dataset(cfg)
    pd.testing.assert_frame_equal(left, right)


def test_generator_contract():
    df = generate_lending_dataset(SyntheticDataConfig(n_samples=2_000, random_seed=42))
    required = {
        "application_id", "device_risk_score", "debt_to_income", "credit_utilization",
        "sex", "age_group", "synthetic_demographic_group", "default_30d",
    }
    assert required.issubset(df.columns)
    assert set(df["default_30d"].unique()).issubset({0, 1})
    observed = df["device_risk_score"].dropna()
    assert observed.between(0, 1).all()
