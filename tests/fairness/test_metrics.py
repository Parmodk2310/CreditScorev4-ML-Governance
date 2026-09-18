from __future__ import annotations

import numpy as np

from creditscore.fairness.metrics import approval_rate


def test_approval_rate_uses_favorable_non_default_decision() -> None:
    y_true = np.array([0, 1, 0, 1])
    predicted_default = np.array([0, 1, 0, 0])
    assert approval_rate(y_true, predicted_default) == 0.75
