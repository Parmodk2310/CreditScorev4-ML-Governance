import numpy as np
import pandas as pd

from creditscore.drift.psi import calculate_psi


def test_identical_distribution_has_zero_psi() -> None:
    values = pd.Series(np.linspace(0.0, 1.0, 1000))
    assert calculate_psi(values, values) < 1e-12


def test_shifted_distribution_has_critical_psi() -> None:
    reference = pd.Series(np.linspace(0.0, 1.0, 2000))
    current = (reference + 0.20).clip(0.0, 1.0)
    assert calculate_psi(reference, current) >= 0.20
