"""Fairlearn metric helpers with explicit lending decision semantics."""

from __future__ import annotations

import numpy as np


def approval_rate(y_true, y_pred) -> float:
    """Return favorable-decision rate where predicted default=0 means approved."""
    del y_true
    labels = np.asarray(y_pred, dtype=int)
    return float((labels == 0).mean())
