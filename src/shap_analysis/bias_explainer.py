"""
SHAP-based Bias Attribution for CreditScoreV4.
Identifies which features contribute most to unfair predictions across groups.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import shap
from loguru import logger


class SHAPBiasAttributor:
    """
    Uses SHAP values to attribute bias to specific features.
    
    When the 11pp minority approval rate drop occurred, this would have
    identified that device_risk_score (with its shifted distribution)
    was the primary driver of disparate impact.
    """
    
    def __init__(self, model, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        self.shap_values = None
    
    def fit_explainer(self, X_background: pd.DataFrame):
        """Initialize SHAP TreeExplainer with background data."""
        self.explainer = shap.TreeExplainer(self.model)
        logger.info("SHAP TreeExplainer initialized")
    
    def explain(self, X: pd.DataFrame) -> np.ndarray:
        """Generate SHAP values for predictions."""
        if self.explainer is None:
            self.fit_explainer(X.sample(min(100, len(X))))
        
        self.shap_values = self.explainer.shap_values(X)
        logger.info(f"Generated SHAP values: shape {np.array(self.shap_values).shape}")
        return self.shap_values
    
    def attribute_bias_by_group(
        self,
        X: pd.DataFrame,
        protected_attribute: str,
        protected_values: List[str],
    ) -> Dict[str, Any]:
        """
        Attribute bias to features by comparing SHAP distributions across groups.
        
        Returns:
            Dictionary with bias attribution per feature per group.
        """
        if self.shap_values is None:
            self.explain(X)
        
        results = {}
        
        for value in protected_values:
            mask = X[protected_attribute] == value
            group_shap = np.array(self.shap_values)[mask.values]
            group_features = X[mask]
            
            # Mean absolute SHAP per feature
            mean_abs_shap = np.abs(group_shap).mean(axis=0)
            
            # Feature ranking by importance
            feature_importance = pd.DataFrame({
                "feature": self.feature_names[:len(mean_abs_shap)],
                "mean_abs_shap": mean_abs_shap,
            }).sort_values("mean_abs_shap", ascending=False)
            
            results[value] = {
                "group_size": int(mask.sum()),
                "top_biased_features": feature_importance.head(10).to_dict("records"),
                "mean_prediction": float(self.model.predict_proba(group_features)[:, 1].mean()),
            }
        
        # Compare groups to identify bias drivers
        reference = protected_values[0]
        comparison = {}
        
        for value in protected_values[1:]:
            ref_shap = np.abs(np.array(self.shap_values)[X[protected_attribute] == reference].mean(axis=0))
            comp_shap = np.abs(np.array(self.shap_values)[X[protected_attribute] == value].mean(axis=0))
            
            # Features with largest difference in SHAP contribution
            diff = np.abs(ref_shap - comp_shap)
            diff_df = pd.DataFrame({
                "feature": self.feature_names[:len(diff)],
                "shap_difference": diff,
            }).sort_values("shap_difference", ascending=False)
            
            comparison[f"{reference}_vs_{value}"] = {
                "top_bias_drivers": diff_df.head(10).to_dict("records"),
                "max_difference": float(diff.max()),
            }
        
        return {
            "protected_attribute": protected_attribute,
            "group_analysis": results,
            "group_comparisons": comparison,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def generate_bias_report(self, attribution: Dict[str, Any]) -> str:
        """Generate human-readable bias attribution report."""
        lines = [
            "=" * 60,
            "SHAP BIAS ATTRIBUTION REPORT",
            "=" * 60,
            f"Protected Attribute: {attribution['protected_attribute']}",
            "-" * 60,
        ]
        
        for comparison, data in attribution["group_comparisons"].items():
            lines.append(f"\n{comparison}:")
            lines.append("Top Bias Drivers (features with divergent impact):")
            for driver in data["top_bias_drivers"][:5]:
                lines.append(f"  • {driver['feature']}: ΔSHAP = {driver['shap_difference']:.4f}")
        
        lines.append("=" * 60)
        return "\n".join(lines)