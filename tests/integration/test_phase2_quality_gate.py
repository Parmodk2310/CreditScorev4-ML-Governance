from pathlib import Path

import pandas as pd

from creditscore.validation import DataQualityGate, load_data_contract

ROOT = Path(__file__).resolve().parents[2]


def test_phase2_blocks_same_vendor_b_batch_that_degraded_phase1_model(tmp_path: Path):
    healthy = pd.read_csv(ROOT / "data" / "raw" / "vendor_a" / "holdout.csv")
    incident = pd.read_csv(ROOT / "data" / "raw" / "vendor_b" / "holdout.csv")
    contract = load_data_contract(ROOT / "contracts" / "credit_application_contract.yaml")
    gate = DataQualityGate(
        contract, evidence_dir=tmp_path / "evidence", quarantine_dir=tmp_path / "quarantine"
    )

    healthy_decision = gate.evaluate(healthy, batch_name="vendor_a", source="vendor_a")
    incident_decision = gate.evaluate(incident, batch_name="vendor_b", source="vendor_b")

    assert healthy_decision.passed
    assert not incident_decision.passed
    assert incident["device_risk_score"].isna().mean() == 0.22
    assert "device_risk_score.null_rate" in incident_decision.failed_rule_ids
