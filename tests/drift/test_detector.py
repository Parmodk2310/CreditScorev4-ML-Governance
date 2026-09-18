import numpy as np
import pandas as pd

from creditscore.drift.detector import DriftDetector


def _config() -> dict:
    return {
        "scenario": {"name": "test", "reference_source": "a", "source": "c"},
        "monitoring": {
            "features": ["stable", "shifted"],
            "psi": {"bins": 10, "epsilon": 1e-6, "warning": 0.10, "critical": 0.20},
            "ks": {"warning": 0.05, "critical": 0.10, "alpha": 0.05},
        },
    }


def test_detector_separates_stable_and_shifted_features() -> None:
    stable = np.linspace(0.0, 1.0, 2000)
    reference = pd.DataFrame({"stable": stable, "shifted": stable})
    current = pd.DataFrame({"stable": stable, "shifted": np.clip(stable + 0.20, 0.0, 1.0)})
    detector = DriftDetector(_config())
    predictions = pd.Series(stable)
    report = detector.evaluate(
        reference,
        current,
        reference_predictions=predictions,
        current_predictions=predictions,
        approval_threshold=0.5,
    )
    results = {result.feature: result for result in report.feature_results}
    assert results["stable"].status == "STABLE"
    assert results["shifted"].status == "CRITICAL"
    assert report.overall_status == "CRITICAL"
