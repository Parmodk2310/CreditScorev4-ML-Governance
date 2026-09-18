"""Population Stability Index using reference-derived quantile bins."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _reference_edges(reference: np.ndarray, bins: int) -> np.ndarray:
    quantiles = np.linspace(0.0, 1.0, bins + 1)
    edges = np.unique(np.quantile(reference, quantiles))
    if len(edges) < 3:
        minimum = float(np.min(reference))
        maximum = float(np.max(reference))
        if minimum == maximum:
            return np.array([-np.inf, np.inf], dtype=float)
        edges = np.linspace(minimum, maximum, bins + 1)
    edges = edges.astype(float)
    edges[0] = -np.inf
    edges[-1] = np.inf
    return edges


def _distribution(values: pd.Series, edges: np.ndarray, epsilon: float) -> np.ndarray:
    numeric = pd.to_numeric(values, errors="coerce")
    total = len(numeric)
    if total == 0:
        raise ValueError("PSI requires non-empty samples")

    clean = numeric.dropna().to_numpy(dtype=float)
    counts, _ = np.histogram(clean, bins=edges)
    missing_count = int(numeric.isna().sum())
    proportions = np.concatenate([counts.astype(float), np.array([missing_count], dtype=float)]) / total
    return np.clip(proportions, epsilon, None)


def calculate_psi(
    reference: pd.Series,
    current: pd.Series,
    *,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    """Calculate PSI with fixed bins learned only from the reference sample."""
    reference_numeric = pd.to_numeric(reference, errors="coerce").dropna().to_numpy(dtype=float)
    if reference_numeric.size == 0:
        raise ValueError("Reference sample has no numeric observations")
    edges = _reference_edges(reference_numeric, bins)
    expected = _distribution(reference, edges, epsilon)
    actual = _distribution(current, edges, epsilon)
    return float(np.sum((actual - expected) * np.log(actual / expected)))
