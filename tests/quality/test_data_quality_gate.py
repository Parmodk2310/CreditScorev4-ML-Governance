from pathlib import Path

import pandas as pd

from creditscore.validation import DataQualityGate, load_data_contract

ROOT = Path(__file__).resolve().parents[2]


def _gate(tmp_path: Path) -> DataQualityGate:
    contract = load_data_contract(ROOT / "contracts" / "credit_application_contract.yaml")
    return DataQualityGate(
        contract,
        evidence_dir=tmp_path / "evidence",
        quarantine_dir=tmp_path / "quarantine",
    )


def test_healthy_batch_is_not_quarantined(tmp_path: Path):
    frame = pd.read_csv(ROOT / "data" / "raw" / "vendor_a" / "holdout.csv")
    decision = _gate(tmp_path).evaluate(frame, batch_name="healthy", source="vendor_a")
    assert decision.passed
    assert decision.quarantine_path is None
    assert Path(decision.evidence_path).exists()


def test_exact_phase1_vendor_b_fixture_is_blocked_and_quarantined(tmp_path: Path):
    frame = pd.read_csv(ROOT / "data" / "raw" / "vendor_b" / "holdout.csv")
    decision = _gate(tmp_path).evaluate(frame, batch_name="vendor_b", source="vendor_b")
    assert not decision.passed
    assert "device_risk_score.null_rate" in decision.failed_rule_ids
    assert decision.quarantine_path is not None
    assert Path(decision.quarantine_path).exists()
