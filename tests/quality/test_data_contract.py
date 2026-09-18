from pathlib import Path

import pandas as pd

from creditscore.validation import DataContractValidator, load_data_contract

ROOT = Path(__file__).resolve().parents[2]


def _contract():
    return load_data_contract(ROOT / "contracts" / "credit_application_contract.yaml")


def test_healthy_phase1_batch_passes_contract():
    frame = pd.read_csv(ROOT / "data" / "raw" / "vendor_a" / "holdout.csv")
    report = DataContractValidator(_contract()).validate(frame, batch_name="healthy", source="vendor_a")
    assert report.passed


def test_phase1_incident_fails_device_null_contract():
    frame = pd.read_csv(ROOT / "data" / "raw" / "vendor_b" / "holdout.csv")
    report = DataContractValidator(_contract()).validate(frame, batch_name="incident", source="vendor_b")
    assert not report.passed
    assert "device_risk_score.null_rate" in report.failed_rule_ids


def test_missing_required_column_is_rejected():
    frame = pd.read_csv(ROOT / "data" / "raw" / "vendor_a" / "holdout.csv").drop(columns=["annual_income"])
    report = DataContractValidator(_contract()).validate(frame, batch_name="missing_column", source="test")
    assert not report.passed
    assert "schema.required_columns" in report.failed_rule_ids
