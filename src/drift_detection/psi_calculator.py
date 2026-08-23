"""
Population Stability Index (PSI) Calculator for CreditScoreV4.
Implements feature-level and score-level PSI monitoring with automated triggers.

PSI Thresholds:
- < 0.1: No significant change (green)
- 0.1 - 0.2: Moderate change (yellow/warning)
- > 0.2: Significant change (red/critical)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger


@dataclass
class PSIDriftConfig:
    """Configuration for PSI drift detection."""
    
    # PSI thresholds
    warning_threshold: float = 0.1
    critical_threshold: float = 0.2
    
    # Binning strategy
    bin_strategy: str = "quantile"  # quantile, fixed
    num_bins: int = 10
    
    # Features to monitor
    features_to_monitor: List[str] = field(default_factory=lambda: [
        "device_risk_score",
        "debt_to_income_ratio",
        "annual_income",
        "credit_history_length",
    ])
    
    # Score monitoring
    monitor_score: bool = True
    score_column: str = "predicted_score"
    
    # KS test
    ks_test_enabled: bool = True
    ks_alpha: float = 0.05
    
    # Reporting
    report_path: str = "data/validation/drift_reports"


class PSICalculator:
    """
    Population Stability Index calculator.
    
    PSI measures the shift in distribution between a baseline (reference)
    and current dataset. It was critical in detecting the device_risk_score
    distribution shift from 0.31 to 0.44 mean during the incident.
    """
    
    def __init__(self, config: Optional[PSIDriftConfig] = None):
        self.config = config or PSIDriftConfig()
        self.baseline_distributions: Dict[str, Dict[str, Any]] = {}
        self.baseline_bins: Dict[str, np.ndarray] = {}
    
    def _create_bins(
        self,
        data: np.ndarray,
        strategy: str = "quantile",
        num_bins: int = 10,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create bins for PSI calculation.
        
        Returns:
            Tuple of (bin_edges, bin_counts)
        """
        data = data[~np.isnan(data)]
        
        if strategy == "quantile":
            # Use quantile-based bins (equal frequency)
            quantiles = np.linspace(0, 1, num_bins + 1)
            bin_edges = np.quantile(data, quantiles)
        else:
            # Use fixed-width bins
            min_val, max_val = data.min(), data.max()
            bin_edges = np.linspace(min_val, max_val, num_bins + 1)
        
        # Ensure unique edges
        bin_edges = np.unique(bin_edges)
        if len(bin_edges) < 3:
            # Fallback for very concentrated data
            bin_edges = np.array([data.min(), data.mean(), data.max()])
        
        # Calculate counts
        counts, _ = np.histogram(data, bins=bin_edges)
        
        # Handle empty bins by merging
        counts = counts.astype(float)
        counts[counts == 0] = 0.0001  # Small epsilon to avoid division by zero
        
        proportions = counts / counts.sum()
        
        return bin_edges, proportions
    
    def fit_baseline(self, df: pd.DataFrame, features: Optional[List[str]] = None):
        """
        Fit baseline distributions from reference data.
        
        Args:
            df: Reference DataFrame
            features: List of features to monitor (uses config default if None)
        """
        features = features or self.config.features_to_monitor
        
        logger.info(f"Fitting baseline distributions for {len(features)} features")
        
        for feature in features:
            if feature not in df.columns:
                logger.warning(f"Feature {feature} not found in baseline data")
                continue
            
            data = df[feature].dropna().values
            
            if len(data) == 0:
                logger.warning(f"No valid data for feature {feature}")
                continue
            
            bin_edges, proportions = self._create_bins(
                data,
                strategy=self.config.bin_strategy,
                num_bins=self.config.num_bins,
            )
            
            self.baseline_bins[feature] = bin_edges
            self.baseline_distributions[feature] = {
                "bin_edges": bin_edges.tolist(),
                "proportions": proportions.tolist(),
                "mean": float(np.mean(data)),
                "std": float(np.std(data)),
                "median": float(np.median(data)),
                "min": float(np.min(data)),
                "max": float(np.max(data)),
                "n_samples": len(data),
                "fitted_at": datetime.now(timezone.utc).isoformat(),
            }
            
            logger.info(
                f"Baseline for {feature}: mean={self.baseline_distributions[feature]['mean']:.4f}, "
                f"std={self.baseline_distributions[feature]['std']:.4f}"
            )
    
    def calculate_psi(
        self,
        baseline_proportions: np.ndarray,
        current_proportions: np.ndarray,
    ) -> float:
        """
        Calculate PSI between two distributions.
        
        PSI = sum((Actual% - Expected%) * ln(Actual% / Expected%))
        
        Args:
            baseline_proportions: Expected distribution proportions
            current_proportions: Actual distribution proportions
            
        Returns:
            PSI value
        """
        # Ensure same length
        min_len = min(len(baseline_proportions), len(current_proportions))
        baseline_proportions = baseline_proportions[:min_len]
        current_proportions = current_proportions[:min_len]
        
        # Add epsilon to avoid log(0)
        epsilon = 0.0001
        baseline_proportions = np.maximum(baseline_proportions, epsilon)
        current_proportions = np.maximum(current_proportions, epsilon)
        
        # Normalize to ensure proportions sum to 1
        baseline_proportions = baseline_proportions / baseline_proportions.sum()
        current_proportions = current_proportions / current_proportions.sum()
        
        # Calculate PSI
        psi_values = (current_proportions - baseline_proportions) * np.log(
            current_proportions / baseline_proportions
        )
        psi = float(np.sum(psi_values))
        
        return psi
    
    def detect_feature_drift(
        self,
        df: pd.DataFrame,
        feature: str,
    ) -> Dict[str, Any]:
        """
        Detect drift for a single feature.
        
        Args:
            df: Current DataFrame
            feature: Feature name to check
            
        Returns:
            Drift detection results
        """
        if feature not in self.baseline_distributions:
            raise ValueError(f"No baseline for feature {feature}. Call fit_baseline() first.")
        
        data = df[feature].dropna().values
        
        if len(data) == 0:
            return {
                "feature": feature,
                "drift_detected": True,
                "psi": float("inf"),
                "status": "error",
                "message": "No valid data in current dataset",
            }
        
        # Use baseline bins
        bin_edges = self.baseline_bins[feature]
        counts, _ = np.histogram(data, bins=bin_edges)
        counts = counts.astype(float)
        counts[counts == 0] = 0.0001
        current_proportions = counts / counts.sum()
        
        baseline_proportions = np.array(self.baseline_distributions[feature]["proportions"])
        
        # Calculate PSI
        psi = self.calculate_psi(baseline_proportions, current_proportions)
        
        # Determine status
        if psi > self.config.critical_threshold:
            status = "critical"
        elif psi > self.config.warning_threshold:
            status = "warning"
        else:
            status = "stable"
        
        # Calculate additional statistics
        baseline_stats = self.baseline_distributions[feature]
        current_mean = float(np.mean(data))
        current_std = float(np.std(data))
        
        result = {
            "feature": feature,
            "drift_detected": status != "stable",
            "psi": psi,
            "status": status,
            "baseline_stats": {
                "mean": baseline_stats["mean"],
                "std": baseline_stats["std"],
                "median": baseline_stats["median"],
            },
            "current_stats": {
                "mean": current_mean,
                "std": current_std,
                "median": float(np.median(data)),
            },
            "mean_shift": current_mean - baseline_stats["mean"],
            "std_shift": current_std - baseline_stats["std"],
            "n_samples": len(data),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if status != "stable":
            logger.warning(
                f"Drift detected in {feature}: PSI={psi:.4f} ({status}), "
                f"mean shifted from {baseline_stats['mean']:.4f} to {current_mean:.4f}"
            )
        
        return result
    
    def detect_all_drift(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect drift for all monitored features.
        
        Returns:
            Comprehensive drift report
        """
        results = []
        critical_count = 0
        warning_count = 0
        
        for feature in self.config.features_to_monitor:
            if feature not in self.baseline_distributions:
                logger.warning(f"Skipping {feature}: no baseline")
                continue
            
            try:
                result = self.detect_feature_drift(df, feature)
                results.append(result)
                
                if result["status"] == "critical":
                    critical_count += 1
                elif result["status"] == "warning":
                    warning_count += 1
            except Exception as e:
                logger.error(f"Error detecting drift for {feature}: {e}")
                results.append({
                    "feature": feature,
                    "drift_detected": True,
                    "status": "error",
                    "message": str(e),
                })
        
        overall_status = "stable"
        if critical_count > 0:
            overall_status = "critical"
        elif warning_count > 0:
            overall_status = "warning"
        
        report = {
            "overall_status": overall_status,
            "drift_detected": overall_status != "stable",
            "critical_features": critical_count,
            "warning_features": warning_count,
            "stable_features": len(results) - critical_count - warning_count,
            "total_features": len(results),
            "thresholds": {
                "warning": self.config.warning_threshold,
                "critical": self.config.critical_threshold,
            },
            "feature_results": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        logger.info(
            f"Drift detection complete: {critical_count} critical, "
            f"{warning_count} warning, {report['stable_features']} stable"
        )
        
        return report
    
    def detect_score_drift(
        self,
        baseline_scores: np.ndarray,
        current_scores: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Detect drift at the model score level.
        
        This is useful for overall model output drift detection.
        """
        # Create bins from baseline scores
        bin_edges, baseline_props = self._create_bins(
            baseline_scores,
            strategy=self.config.bin_strategy,
            num_bins=self.config.num_bins,
        )
        
        # Calculate current proportions using same bins
        counts, _ = np.histogram(current_scores, bins=bin_edges)
        counts = counts.astype(float)
        counts[counts == 0] = 0.0001
        current_props = counts / counts.sum()
        
        psi = self.calculate_psi(baseline_props, current_props)
        
        # KS test
        ks_stat, ks_pvalue = stats.ks_2samp(baseline_scores, current_scores)
        
        status = "stable"
        if psi > self.config.critical_threshold:
            status = "critical"
        elif psi > self.config.warning_threshold:
            status = "warning"
        
        return {
            "level": "score",
            "drift_detected": status != "stable",
            "psi": psi,
            "status": status,
            "ks_statistic": float(ks_stat),
            "ks_pvalue": float(ks_pvalue),
            "ks_significant": ks_pvalue < self.config.ks_alpha,
            "baseline_mean": float(np.mean(baseline_scores)),
            "current_mean": float(np.mean(current_scores)),
            "mean_shift": float(np.mean(current_scores) - np.mean(baseline_scores)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """Save drift report to file."""
        Path(self.config.report_path).mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            filename = f"drift_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = Path(self.config.report_path) / filename
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Saved drift report to {filepath}")
        return str(filepath)
    
    def save_baseline(self, path: str):
        """Save baseline distributions to file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({
                "distributions": self.baseline_distributions,
                "config": {
                    "bin_strategy": self.config.bin_strategy,
                    "num_bins": self.config.num_bins,
                    "warning_threshold": self.config.warning_threshold,
                    "critical_threshold": self.config.critical_threshold,
                },
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }, f, indent=2, default=str)
        
        logger.info(f"Saved baseline to {path}")
    
    @classmethod
    def load_baseline(cls, path: str) -> "PSICalculator":
        """Load baseline distributions from file."""
        with open(path, "r") as f:
            data = json.load(f)
        
        config = PSIDriftConfig(**data["config"])
        calculator = cls(config)
        calculator.baseline_distributions = data["distributions"]
        
        # Reconstruct bins
        for feature, dist in calculator.baseline_distributions.items():
            calculator.baseline_bins[feature] = np.array(dist["bin_edges"])
        
        logger.info(f"Loaded baseline from {path} with {len(calculator.baseline_distributions)} features")
        return calculator


if __name__ == "__main__":
    # Example: Simulate the incident
    np.random.seed(42)
    
    # Baseline: device_risk_score ~ N(0.31, 0.15)
    baseline_df = pd.DataFrame({
        "device_risk_score": np.random.normal(0.31, 0.15, 10000).clip(0, 1),
        "debt_to_income_ratio": np.random.beta(2, 5, 10000),
    })
    
    # Current: device_risk_score shifted to N(0.44, 0.15) - THE INCIDENT
    current_df = pd.DataFrame({
        "device_risk_score": np.random.normal(0.44, 0.15, 10000).clip(0, 1),
        "debt_to_income_ratio": np.random.beta(2, 5, 10000),
    })
    
    calculator = PSICalculator()
    calculator.fit_baseline(baseline_df)
    
    report = calculator.detect_all_drift(current_df)
    print(json.dumps(report, indent=2, default=str))