from pathlib import Path

import pandas as pd

from creditscore.data.preprocessing import MODEL_INPUT_FEATURES
from creditscore.drift import DriftDetector
from creditscore.incidents.vendor_c_drift import VendorCDriftConfig, VendorCDriftScenario
from creditscore.model.train import load_model
from creditscore.utils.config import load_yaml
from creditscore.validation.contract import load_data_contract
from creditscore.validation.validator import DataContractValidator

ROOT = Path(__file__).resolve().parents[2]


def test_contract_valid_vendor_c_is_detected_as_drift() -> None:
    phase3 = load_yaml(ROOT / "configs/phase3.yaml")
    reference = pd.read_csv(ROOT / "data/raw/vendor_a/holdout.csv")
    current = VendorCDriftScenario(VendorCDriftConfig()).apply(reference)

    contract = load_data_contract(ROOT / "contracts/credit_application_contract.yaml")
    quality = DataContractValidator(contract).validate(current, batch_name="vendor_c", source="vendor_c")
    assert quality.passed

    model = load_model(ROOT / phase3["paths"]["model"])
    reference_predictions = pd.Series(model.predict_proba(reference[MODEL_INPUT_FEATURES])[:, 1])
    current_predictions = pd.Series(model.predict_proba(current[MODEL_INPUT_FEATURES])[:, 1])

    report = DriftDetector(phase3).evaluate(
        reference,
        current,
        reference_predictions=reference_predictions,
        current_predictions=current_predictions,
        approval_threshold=float(phase3["prediction"]["approval_threshold"]),
    )
    results = {result.feature: result for result in report.feature_results}
    assert results["annual_income"].status == "STABLE"
    assert results["device_risk_score"].status == "CRITICAL"
    assert report.overall_status == "CRITICAL"
