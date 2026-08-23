"""
Fairness Monitoring Framework for CreditScoreV4.
Implements Demographic Parity, Equal Opportunity, Disparate Impact (4/5ths rule),
and Equalized Odds with automated compliance checking.

Regulatory Context:
- ECOA (Equal Credit Opportunity Act)
- Fair Lending regulations
- 4/5ths rule compliance (Disparate Impact Ratio >= 0.80)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class FairnessConfig:
    """Configuration for fairness monitoring."""
    
    # Protected attributes
    protected_attributes: List[str] = field(default_factory=lambda: ["race", "gender", "age_group"])
    
    # Fairness thresholds
    demographic_parity_threshold: float = 0.05  # Max 5pp difference
    equal_opportunity_threshold: float = 0.05
    equalized_odds_threshold: float = 0.05
    disparate_impact_threshold: float = 0.80  # 4/5ths rule
    calibration_threshold: float = 0.05
    
    # Reference group (for ratio calculations)
    reference_groups: Dict[str, str] = field(default_factory=lambda: {
        "race": "White",
        "gender": "Male",
        "age_group": "26-35",
    })
    
    # Reporting
    report_path: str = "data/validation/fairness_reports"
    
    # Approval threshold
    approval_threshold: float = 0.5


class FairnessMetricsCalculator:
    """
    Calculate fairness metrics for credit scoring models.
    
    The 11pp minority approval rate drop during the incident would have been
caught by the Demographic Parity and Disparate Impact metrics.
    """
    
    def __init__(self, config: Optional[FairnessConfig] = None):
        self.config = config or FairnessConfig()
        self.results: Dict[str, Any] = {}
    
    def _get_group_mask(
        self,
        df: pd.DataFrame,
        attribute: str,
        group_value: Any,
    ) -> pd.Series:
        """Get boolean mask for a specific group."""
        return df[attribute] == group_value
    
    def _get_group_stats(
        self,
        df: pd.DataFrame,
        attribute: str,
        group_value: Any,
        score_col: str = "predicted_score",
        target_col: str = "delinquent",
    ) -> Dict[str, float]:
        """Calculate statistics for a specific group."""
        mask = self._get_group_mask(df, attribute, group_value)
        group_df = df[mask]
        
        if len(group_df) == 0:
            return {
                "count": 0,
                "positive_rate": 0.0,
                "approval_rate": 0.0,
                "default_rate": 0.0,
                "mean_score": 0.0,
            }
        
        scores = group_df[score_col].values
        targets = group_df[target_col].values
        
        approvals = scores >= self.config.approval_threshold
        
        return {
            "count": len(group_df),
            "positive_rate": float(targets.mean()),
            "approval_rate": float(approvals.mean()),
            "default_rate": float(targets[approvals].mean()) if approvals.sum() > 0 else 0.0,
            "mean_score": float(scores.mean()),
            "median_score": float(np.median(scores)),
        }
    
    def demographic_parity(
        self,
        df: pd.DataFrame,
        attribute: str,
        score_col: str = "predicted_score",
    ) -> Dict[str, Any]:
        """
        Calculate Demographic Parity.
        
        Demographic Parity: P(Ŷ=1 | A=a) should be equal across groups.
        Measures: Difference in approval rates between groups.
        """
        groups = df[attribute].unique()
        approval_rates = {}
        
        for group in groups:
            stats = self._get_group_stats(df, attribute, group, score_col)
            approval_rates[group] = stats["approval_rate"]
        
        # Calculate max difference from reference
        reference_group = self.config.reference_groups.get(attribute)
        if reference_group and reference_group in approval_rates:
            ref_rate = approval_rates[reference_group]
            differences = {
                group: abs(rate - ref_rate)
                for group, rate in approval_rates.items()
                if group != reference_group
            }
            max_diff = max(differences.values()) if differences else 0.0
        else:
            # Use overall mean as reference
            mean_rate = np.mean(list(approval_rates.values()))
            differences = {
                group: abs(rate - mean_rate)
                for group, rate in approval_rates.items()
            }
            max_diff = max(differences.values()) if differences else 0.0
        
        violation = max_diff > self.config.demographic_parity_threshold
        
        return {
            "metric": "demographic_parity",
            "attribute": attribute,
            "approval_rates": approval_rates,
            "max_difference": max_diff,
            "threshold": self.config.demographic_parity_threshold,
            "violation": violation,
            "status": "violation" if violation else "pass",
            "details": differences,
        }
    
    def equal_opportunity(
        self,
        df: pd.DataFrame,
        attribute: str,
        score_col: str = "predicted_score",
        target_col: str = "delinquent",
    ) -> Dict[str, Any]:
        """
        Calculate Equal Opportunity Difference.
        
        Equal Opportunity: P(Ŷ=1 | Y=1, A=a) should be equal across groups.
        Measures: Difference in True Positive Rates (TPR) between groups.
        """
        groups = df[attribute].unique()
        tpr_by_group = {}
        
        for group in groups:
            mask = self._get_group_mask(df, attribute, group)
            group_df = df[mask]
            
            # Filter to positive class (actual defaults)
            positive_mask = group_df[target_col] == 1
            if positive_mask.sum() == 0:
                tpr_by_group[group] = 0.0
                continue
            
            positive_df = group_df[positive_mask]
            scores = positive_df[score_col].values
            
            # TPR = P(approved | actual default) - but in credit, we want to catch defaults
            # Actually for credit: TPR = P(rejected | actual default) = recall for positive class
            # But usually we frame as: P(approved | good borrower) - so let's use that
            
            # For credit scoring, equal opportunity means:
            # Among people who actually repay (Y=0), approval rates should be equal
            good_borrowers = group_df[target_col] == 0
            if good_borrowers.sum() == 0:
                tpr_by_group[group] = 0.0
                continue
            
            good_scores = group_df.loc[good_borrowers, score_col].values
            tpr_by_group[group] = float((good_scores >= self.config.approval_threshold).mean())
        
        # Calculate differences
        reference_group = self.config.reference_groups.get(attribute)
        if reference_group and reference_group in tpr_by_group:
            ref_tpr = tpr_by_group[reference_group]
            differences = {
                group: abs(tpr - ref_tpr)
                for group, tpr in tpr_by_group.items()
                if group != reference_group
            }
            max_diff = max(differences.values()) if differences else 0.0
        else:
            mean_tpr = np.mean(list(tpr_by_group.values()))
            differences = {
                group: abs(tpr - mean_tpr)
                for group, tpr in tpr_by_group.items()
            }
            max_diff = max(differences.values()) if differences else 0.0
        
        violation = max_diff > self.config.equal_opportunity_threshold
        
        return {
            "metric": "equal_opportunity",
            "attribute": attribute,
            "tpr_by_group": tpr_by_group,
            "max_difference": max_diff,
            "threshold": self.config.equal_opportunity_threshold,
            "violation": violation,
            "status": "violation" if violation else "pass",
            "details": differences,
        }
    
    def disparate_impact(
        self,
        df: pd.DataFrame,
        attribute: str,
        score_col: str = "predicted_score",
    ) -> Dict[str, Any]:
        """
        Calculate Disparate Impact Ratio (4/5ths rule).
        
        Disparate Impact: Approval rate ratio between groups should be >= 0.80.
        This is the primary legal standard for fair lending.
        """
        groups = df[attribute].unique()
        approval_rates = {}
        
        for group in groups:
            stats = self._get_group_stats(df, attribute, group, score_col)
            approval_rates[group] = stats["approval_rate"]
        
        # Calculate ratios relative to reference group
        reference_group = self.config.reference_groups.get(attribute)
        if reference_group and reference_group in approval_rates:
            ref_rate = approval_rates[reference_group]
            
            if ref_rate == 0:
                ratios = {group: 0.0 for group in groups if group != reference_group}
            else:
                ratios = {
                    group: rate / ref_rate
                    for group, rate in approval_rates.items()
                    if group != reference_group
                }
            
            min_ratio = min(ratios.values()) if ratios else 1.0
        else:
            # Use maximum approval rate as reference
            max_rate = max(approval_rates.values())
            if max_rate == 0:
                ratios = {group: 0.0 for group in groups}
            else:
                ratios = {
                    group: rate / max_rate
                    for group, rate in approval_rates.items()
                }
            min_ratio = min(ratios.values()) if ratios else 1.0
        
        violation = min_ratio < self.config.disparate_impact_threshold
        
        return {
            "metric": "disparate_impact",
            "attribute": attribute,
            "approval_rates": approval_rates,
            "ratios": ratios,
            "min_ratio": min_ratio,
            "threshold": self.config.disparate_impact_threshold,
            "violation": violation,
            "status": "violation" if violation else "pass",
            "legal_standard": "4/5ths rule (ratio >= 0.80)",
        }
    
    def equalized_odds(
        self,
        df: pd.DataFrame,
        attribute: str,
        score_col: str = "predicted_score",
        target_col: str = "delinquent",
    ) -> Dict[str, Any]:
        """
        Calculate Equalized Odds.
        
        Equalized Odds: Both TPR and FPR should be equal across groups.
        """
        groups = df[attribute].unique()
        tpr_by_group = {}
        fpr_by_group = {}
        
        for group in groups:
            mask = self._get_group_mask(df, attribute, group)
            group_df = df[mask]
            
            scores = group_df[score_col].values
            targets = group_df[target_col].values
            predictions = scores >= self.config.approval_threshold
            
            # TPR (True Positive Rate) - among actual positives
            actual_positives = targets == 1
            if actual_positives.sum() > 0:
                tpr_by_group[group] = float(
                    predictions[actual_positives].mean()
                )
            else:
                tpr_by_group[group] = 0.0
            
            # FPR (False Positive Rate) - among actual negatives
            actual_negatives = targets == 0
            if actual_negatives.sum() > 0:
                fpr_by_group[group] = float(
                    predictions[actual_negatives].mean()
                )
            else:
                fpr_by_group[group] = 0.0
        
        # Calculate max differences
        reference_group = self.config.reference_groups.get(attribute)
        if reference_group and reference_group in tpr_by_group:
            ref_tpr = tpr_by_group[reference_group]
            ref_fpr = fpr_by_group[reference_group]
            
            tpr_diffs = {
                group: abs(tpr - ref_tpr)
                for group, tpr in tpr_by_group.items()
                if group != reference_group
            }
            fpr_diffs = {
                group: abs(fpr - ref_fpr)
                for group, fpr in fpr_by_group.items()
                if group != reference_group
            }
            
            max_tpr_diff = max(tpr_diffs.values()) if tpr_diffs else 0.0
            max_fpr_diff = max(fpr_diffs.values()) if fpr_diffs else 0.0
        else:
            mean_tpr = np.mean(list(tpr_by_group.values()))
            mean_fpr = np.mean(list(fpr_by_group.values()))
            
            tpr_diffs = {group: abs(tpr - mean_tpr) for group, tpr in tpr_by_group.items()}
            fpr_diffs = {group: abs(fpr - mean_fpr) for group, fpr in fpr_by_group.items()}
            
            max_tpr_diff = max(tpr_diffs.values()) if tpr_diffs else 0.0
            max_fpr_diff = max(fpr_diffs.values()) if fpr_diffs else 0.0
        
        max_diff = max(max_tpr_diff, max_fpr_diff)
        violation = max_diff > self.config.equalized_odds_threshold
        
        return {
            "metric": "equalized_odds",
            "attribute": attribute,
            "tpr_by_group": tpr_by_group,
            "fpr_by_group": fpr_by_group,
            "max_tpr_difference": max_tpr_diff,
            "max_fpr_difference": max_fpr_diff,
            "max_difference": max_diff,
            "threshold": self.config.equalized_odds_threshold,
            "violation": violation,
            "status": "violation" if violation else "pass",
        }
    
    def calibration_by_group(
        self,
        df: pd.DataFrame,
        attribute: str,
        score_col: str = "predicted_score",
        target_col: str = "delinquent",
        n_bins: int = 10,
    ) -> Dict[str, Any]:
        """
        Check calibration within each group.
        
        Calibration: Predicted probability should match actual default rate.
        """
        groups = df[attribute].unique()
        calibration_by_group = {}
        
        for group in groups:
            mask = self._get_group_mask(df, attribute, group)
            group_df = df[mask]
            
            if len(group_df) < n_bins:
                calibration_by_group[group] = {"error": "Insufficient data"}
                continue
            
            scores = group_df[score_col].values
            targets = group_df[target_col].values
            
            # Create score bins
            score_bins = pd.qcut(scores, q=n_bins, duplicates="drop")
            
            calibration_data = []
            for bin_name, bin_df in group_df.groupby(score_bins):
                if len(bin_df) == 0:
                    continue
                
                mean_score = bin_df[score_col].mean()
                actual_rate = bin_df[target_col].mean()
                
                calibration_data.append({
                    "bin": str(bin_name),
                    "mean_predicted": float(mean_score),
                    "actual_rate": float(actual_rate),
                    "count": len(bin_df),
                    "error": float(abs(mean_score - actual_rate)),
                })
            
            # Calculate max calibration error
            max_error = max(d["error"] for d in calibration_data) if calibration_data else 0.0
            
            calibration_by_group[group] = {
                "max_calibration_error": max_error,
                "bins": calibration_data,
            }
        
        # Check if any group exceeds threshold
        max_errors = [
            data["max_calibration_error"]
            for data in calibration_by_group.values()
            if "max_calibration_error" in data
        ]
        overall_max_error = max(max_errors) if max_errors else 0.0
        
        violation = overall_max_error > self.config.calibration_threshold
        
        return {
            "metric": "calibration",
            "attribute": attribute,
            "calibration_by_group": calibration_by_group,
            "max_calibration_error": overall_max_error,
            "threshold": self.config.calibration_threshold,
            "violation": violation,
            "status": "violation" if violation else "pass",
        }
    
    def compute_all_metrics(
        self,
        df: pd.DataFrame,
        score_col: str = "predicted_score",
        target_col: str = "delinquent",
    ) -> Dict[str, Any]:
        """
        Compute all fairness metrics for all protected attributes.
        
        Returns:
            Comprehensive fairness report
        """
        all_results = []
        violations = []
        
        for attribute in self.config.protected_attributes:
            if attribute not in df.columns:
                logger.warning(f"Protected attribute {attribute} not found in data")
                continue
            
            logger.info(f"Computing fairness metrics for {attribute}")
            
            # Compute each metric
            dp = self.demographic_parity(df, attribute, score_col)
            eo = self.equal_opportunity(df, attribute, score_col, target_col)
            di = self.disparate_impact(df, attribute, score_col)
            eq_odds = self.equalized_odds(df, attribute, score_col, target_col)
            cal = self.calibration_by_group(df, attribute, score_col, target_col)
            
            attribute_results = {
                "attribute": attribute,
                "metrics": {
                    "demographic_parity": dp,
                    "equal_opportunity": eo,
                    "disparate_impact": di,
                    "equalized_odds": eq_odds,
                    "calibration": cal,
                },
            }
            
            all_results.append(attribute_results)
            
            # Collect violations
            for metric_name, metric_result in attribute_results["metrics"].items():
                if metric_result.get("violation", False):
                    violations.append({
                        "attribute": attribute,
                        "metric": metric_name,
                        "severity": "critical" if metric_name == "disparate_impact" else "warning",
                        "details": metric_result,
                    })
        
        overall_status = "pass"
        if any(v["severity"] == "critical" for v in violations):
            overall_status = "critical"
        elif violations:
            overall_status = "warning"
        
        report = {
            "overall_status": overall_status,
            "violations_detected": len(violations),
            "critical_violations": len([v for v in violations if v["severity"] == "critical"]),
            "warning_violations": len([v for v in violations if v["severity"] == "warning"]),
            "violations": violations,
            "results": all_results,
            "thresholds": {
                "demographic_parity": self.config.demographic_parity_threshold,
                "equal_opportunity": self.config.equal_opportunity_threshold,
                "disparate_impact": self.config.disparate_impact_threshold,
                "equalized_odds": self.config.equalized_odds_threshold,
                "calibration": self.config.calibration_threshold,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        logger.info(
            f"Fairness audit complete: {len(violations)} violations "
            f"({report['critical_violations']} critical, {report['warning_violations']} warning)"
        )
        
        self.results = report
        return report
    
    def save_report(self, report: Optional[Dict[str, Any]] = None, filename: Optional[str] = None):
        """Save fairness report to file."""
        report = report or self.results
        
        Path(self.config.report_path).mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            filename = f"fairness_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = Path(self.config.report_path) / filename
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Saved fairness report to {filepath}")
        return str(filepath)
    
    def generate_compliance_summary(self, report: Optional[Dict[str, Any]] = None) -> str:
        """Generate human-readable compliance summary."""
        report = report or self.results
        
        lines = [
            "=" * 60,
            "FAIRNESS COMPLIANCE REPORT",
            "=" * 60,
            f"Overall Status: {report['overall_status'].upper()}",
            f"Violations: {report['violations_detected']} "
            f"({report['critical_violations']} critical, {report['warning_violations']} warning)",
            "-" * 60,
        ]
        
        for result in report.get("results", []):
            attr = result["attribute"]
            lines.append(f"\\n{attr.upper()}:")
            
            for metric_name, metric_result in result["metrics"].items():
                status = "❌" if metric_result.get("violation") else "✅"
                lines.append(f"  {status} {metric_name}: {metric_result.get('status', 'unknown')}")
                
                if metric_name == "disparate_impact":
                    lines.append(f"     Min Ratio: {metric_result.get('min_ratio', 'N/A'):.3f} "
                               f"(threshold: {metric_result.get('threshold', 'N/A')})")
                elif metric_name == "demographic_parity":
                    lines.append(f"     Max Diff: {metric_result.get('max_difference', 'N/A'):.3f} "
                               f"(threshold: {metric_result.get('threshold', 'N/A')})")
        
        if report["violations"]:
            lines.append("\\n" + "-" * 60)
            lines.append("VIOLATIONS:")
            for v in report["violations"]:
                lines.append(
                    f"  [{v['severity'].upper()}] {v['attribute']} - {v['metric']}"
                )
        
        lines.append("=" * 60)
        
        return "\\n".join(lines)


if __name__ == "__main__":
    # Example: Simulate the 11pp minority approval rate drop
    np.random.seed(42)
    n = 10000
    
    # Simulate biased predictions
    df = pd.DataFrame({
        "race": np.random.choice(["White", "Black", "Asian", "Hispanic"], n),
        "predicted_score": np.random.uniform(0, 1, n),
        "delinquent": np.random.binomial(1, 0.15, n),
    })
    
    # Introduce bias: lower scores for minority groups
    minority_mask = df["race"].isin(["Black", "Hispanic"])
    df.loc[minority_mask, "predicted_score"] *= 0.85  # Reduce scores by 15%
    
    calculator = FairnessMetricsCalculator()
    report = calculator.compute_all_metrics(df)
    
    print(calculator.generate_compliance_summary(report))