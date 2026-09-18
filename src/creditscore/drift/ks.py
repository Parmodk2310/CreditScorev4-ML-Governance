"""Two-sample Kolmogorov-Smirnov drift metric."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scipy.stats import ks_2samp


@dataclass(frozen=True)
class KSResult:
    statistic: float
    pvalue: float
    reference_count: int
    current_count: int


def calculate_ks(reference: pd.Series, current: pd.Series) -> KSResult:
    reference_values = pd.to_numeric(reference, errors="coerce").dropna().to_numpy(dtype=float)
    current_values = pd.to_numeric(current, errors="coerce").dropna().to_numpy(dtype=float)
    if reference_values.size == 0 or current_values.size == 0:
        raise ValueError("KS requires non-empty numeric samples")
    result = ks_2samp(reference_values, current_values, alternative="two-sided", method="auto")
    return KSResult(
        statistic=float(result.statistic),
        pvalue=float(result.pvalue),
        reference_count=int(reference_values.size),
        current_count=int(current_values.size),
    )
