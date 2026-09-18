from creditscore.data.generator import SyntheticDataConfig, generate_lending_dataset
from creditscore.incidents.vendor_migration import VendorMigrationConfig, VendorMigrationIncident


def test_vendor_migration_preserves_schema_and_target():
    healthy = generate_lending_dataset(SyntheticDataConfig(n_samples=5_000, random_seed=42))
    migrated = VendorMigrationIncident(VendorMigrationConfig(target_device_null_rate=0.22)).apply(healthy)
    assert list(migrated.columns) == list(healthy.columns)
    assert migrated["default_30d"].equals(healthy["default_30d"])
    assert 0.215 <= migrated["device_risk_score"].isna().mean() <= 0.225


def test_vendor_migration_changes_device_score_distribution():
    healthy = generate_lending_dataset(SyntheticDataConfig(n_samples=5_000, random_seed=42))
    migrated = VendorMigrationIncident(VendorMigrationConfig()).apply(healthy)
    healthy_std = healthy["device_risk_score"].std()
    migrated_std = migrated["device_risk_score"].std()
    # The silent vendor change compresses the score distribution even though
    # its mean can remain deceptively similar.
    assert migrated_std < healthy_std * 0.80
