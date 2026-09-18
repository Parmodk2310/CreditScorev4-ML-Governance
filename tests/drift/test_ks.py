import numpy as np
import pandas as pd

from creditscore.drift.ks import calculate_ks


def test_identical_distribution_has_zero_ks() -> None:
    values = pd.Series(np.linspace(0.0, 1.0, 1000))
    result = calculate_ks(values, values)
    assert result.statistic == 0.0
    assert result.pvalue == 1.0


def test_shifted_distribution_has_material_ks() -> None:
    reference = pd.Series(np.linspace(0.0, 1.0, 2000))
    current = (reference + 0.20).clip(0.0, 1.0)
    result = calculate_ks(reference, current)
    assert result.statistic >= 0.10
    assert result.pvalue < 0.05
