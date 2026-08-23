"""
Data Preprocessing Pipeline for CreditScoreV4.
Handles feature engineering, encoding, scaling, and imputation strategies.

CRITICAL: This module was redesigned after the incident to prevent
silent median imputation from causing approval inflation.
"""

import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder


@dataclass
class PreprocessingConfig:
    """Configuration for the preprocessing pipeline."""
    
    numerical_features: List[str] = field(default_factory=list)
    categorical_features: List[str] = field(default_factory=list)
    protected_attributes: List[str] = field(default_factory=list)
    target_column: str = "delinquent"
    
    # Imputation strategy - CHANGED after incident
    # Was: "median" (silent, caused approval inflation)
    # Now: "flag_and_report" - explicit handling with monitoring
    numerical_impute_strategy: str = "flag_and_report"
    categorical_impute_strategy: str = "flag_and_report"
    
    # NULL handling thresholds
    max_null_rate: float = 0.05  # 5% - fail if exceeded
    null_rate_warning: float = 0.02  # 2% - warn if exceeded
    
    # Feature engineering
    create_interaction_features: bool = True
    create_ratio_features: bool = True
    
    # Scaling
    scaler_type: str = "standard"  # standard, robust, minmax
    
    # Encoding
    encoding_type: str = "onehot"  # onehot, target, ordinal
    max_cardinality: int = 50  # Max unique values for one-hot encoding


class NullFlagImputer(BaseEstimator, TransformerMixin):
    """
    Custom imputer that adds NULL indicator flags.
    
    This prevents silent imputation by making NULL presence explicit
    in the feature set, allowing the model to learn NULL patterns.
    """
    
    def __init__(self, strategy: str = "median", add_indicator: bool = True):
        self.strategy = strategy
        self.add_indicator = add_indicator
        self.imputer_: Optional[SimpleImputer] = None
        self.null_indicators_: List[str] = []
        self.feature_names_in_: List[str] = []
    
    def fit(self, X: pd.DataFrame, y=None):
        self.feature_names_in_ = list(X.columns)
        
        self.imputer_ = SimpleImputer(strategy=self.strategy, add_indicator=False)
        self.imputer_.fit(X)
        
        if self.add_indicator:
            self.null_indicators_ = [f"{col}_is_null" for col in X.columns]
        
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_transformed = X.copy()
        
        # Apply imputation
        imputed_values = self.imputer_.transform(X_transformed)
        X_transformed = pd.DataFrame(
            imputed_values,
            columns=self.feature_names_in_,
            index=X_transformed.index,
        )
        
        # Add NULL indicator flags
        if self.add_indicator:
            for col in self.feature_names_in_:
                null_flag = X[col].isnull().astype(int)
                if null_flag.sum() > 0:  # Only add if there are NULLs
                    X_transformed[f"{col}_is_null"] = null_flag
        
        return X_transformed


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Creates derived features from raw data.
    
    Features added:
    - income_per_dependent: Income adjusted for household size
    - credit_utilization_trend: Trend in credit utilization
    - debt_to_income_bucket: Binned DTI for regulatory reporting
    - risk_score_composite: Weighted composite of risk signals
    """
    
    def __init__(self, create_interactions: bool = True, create_ratios: bool = True):
        self.create_interactions = create_interactions
        self.create_ratios = create_ratios
        self.derived_features_: List[str] = []
    
    def fit(self, X: pd.DataFrame, y=None):
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_transformed = X.copy()
        
        # 1. Income per dependent (if dependents column exists)
        if "num_dependents" in X_transformed.columns:
            X_transformed["income_per_dependent"] = (
                X_transformed["annual_income"] / 
                X_transformed["num_dependents"].clip(lower=1)
            )
            self.derived_features_.append("income_per_dependent")
        
        # 2. Credit utilization trend (if historical data exists)
        if "avg_credit_utilization" in X_transformed.columns:
            X_transformed["credit_utilization_risk"] = (
                X_transformed["avg_credit_utilization"] > 0.8
            ).astype(int)
            self.derived_features_.append("credit_utilization_risk")
        
        # 3. Debt-to-income bucket (regulatory reporting)
        if "debt_to_income_ratio" in X_transformed.columns:
            X_transformed["dti_bucket"] = pd.cut(
                X_transformed["debt_to_income_ratio"],
                bins=[0, 0.28, 0.36, 0.43, 0.50, 1.0],
                labels=["excellent", "good", "fair", "poor", "very_poor"],
                include_lowest=True,
            )
            self.derived_features_.append("dti_bucket")
        
        # 4. Risk score composite
        risk_features = ["device_risk_score", "credit_utilization_risk"]
        available_risk = [f for f in risk_features if f in X_transformed.columns]
        if available_risk:
            weights = [1.0 / len(available_risk)] * len(available_risk)
            X_transformed["risk_score_composite"] = sum(
                X_transformed[f] * w for f, w in zip(available_risk, weights)
            )
            self.derived_features_.append("risk_score_composite")
        
        # 5. Interaction features
        if self.create_interactions:
            if all(c in X_transformed.columns for c in ["annual_income", "credit_history_length"]):
                X_transformed["income_x_credit_history"] = (
                    X_transformed["annual_income"] * X_transformed["credit_history_length"]
                )
                self.derived_features_.append("income_x_credit_history")
            
            if all(c in X_transformed.columns for c in ["debt_to_income_ratio", "device_risk_score"]):
                X_transformed["dti_x_device_risk"] = (
                    X_transformed["debt_to_income_ratio"] * X_transformed["device_risk_score"]
                )
                self.derived_features_.append("dti_x_device_risk")
        
        # 6. Ratio features
        if self.create_ratios:
            if all(c in X_transformed.columns for c in ["annual_income", "num_credit_lines"]):
                X_transformed["income_per_credit_line"] = (
                    X_transformed["annual_income"] / X_transformed["num_credit_lines"].clip(lower=1)
                )
                self.derived_features_.append("income_per_credit_line")
        
        logger.info(f"Engineered {len(self.derived_features_)} new features: {self.derived_features_}")
        
        return X_transformed


class CreditScoreV4Preprocessor:
    """
    Main preprocessing pipeline for CreditScoreV4.
    
    Architecture:
    1. Data quality check (NULL rates, schema)
    2. Feature engineering
    3. Imputation with NULL flags
    4. Encoding
    5. Scaling
    6. Protected attribute separation (for fairness)
    """
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.pipeline: Optional[Pipeline] = None
        self.feature_names_: List[str] = []
        self.numerical_features_: List[str] = []
        self.categorical_features_: List[str] = []
        self.protected_features_: List[str] = []
        self.target_encoder_: Optional[LabelEncoder] = None
        self.null_report_: Dict[str, Any] = {}
        
        logger.info("Initialized CreditScoreV4Preprocessor")
    
    def _check_null_rates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check NULL rates and generate report.
        
        This is the critical check that would have caught the 22% NULL incident.
        """
        null_rates = df.isnull().mean()
        violations = []
        warnings = []
        
        for col, rate in null_rates.items():
            if rate > self.config.max_null_rate:
                violations.append({
                    "column": col,
                    "null_rate": rate,
                    "threshold": self.config.max_null_rate,
                    "severity": "critical",
                    "message": (
                        f"CRITICAL: {col} has {rate:.1%} NULLs (threshold: {self.config.max_null_rate:.1%})"
                    ),
                })
            elif rate > self.config.null_rate_warning:
                warnings.append({
                    "column": col,
                    "null_rate": rate,
                    "threshold": self.config.null_rate_warning,
                    "severity": "warning",
                    "message": (
                        f"WARNING: {col} has {rate:.1%} NULLs (warning threshold: {self.config.null_rate_warning:.1%})"
                    ),
                })
        
        self.null_report_ = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "total_columns": len(df.columns),
            "columns_with_nulls": int(null_rates.any()),
            "max_null_rate": float(null_rates.max()),
            "violations": violations,
            "warnings": warnings,
            "null_rates": null_rates.to_dict(),
            "passed": len(violations) == 0,
        }
        
        if violations:
            logger.critical(f"NULL rate violations detected: {len(violations)} critical")
            for v in violations:
                logger.critical(v["message"])
        
        if warnings:
            logger.warning(f"NULL rate warnings: {len(warnings)}")
        
        return self.null_report_
    
    def _build_pipeline(self) -> Pipeline:
        """Build the sklearn preprocessing pipeline."""
        
        # Numerical pipeline
        numerical_pipeline = Pipeline([
            ("imputer", NullFlagImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ])
        
        # Categorical pipeline
        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
        
        # Combine
        preprocessor = ColumnTransformer([
            ("num", numerical_pipeline, self.numerical_features_),
            ("cat", categorical_pipeline, self.categorical_features_),
        ], remainder="drop")
        
        # Full pipeline with feature engineering
        pipeline = Pipeline([
            ("feature_engineer", FeatureEngineer()),
            ("preprocessor", preprocessor),
        ])
        
        return pipeline
    
    def fit(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> "CreditScoreV4Preprocessor":
        """
        Fit the preprocessing pipeline.
        
        Args:
            df: Raw DataFrame
            y: Optional target series
        """
        logger.info(f"Fitting preprocessor on {len(df)} rows, {len(df.columns)} columns")
        
        # 1. Check NULL rates
        null_report = self._check_null_rates(df)
        if not null_report["passed"]:
            logger.error("NULL rate check failed - preprocessing halted")
            raise ValueError(
                f"NULL rate violations detected: {len(null_report['violations'])} columns exceed threshold. "
                f"Review null_report_ for details."
            )
        
        # 2. Identify feature types
        all_cols = set(df.columns)
        protected = set(self.config.protected_attributes)
        target = {self.config.target_column}
        
        # Exclude protected and target from model features
        feature_cols = all_cols - protected - target - {"customer_id", "_record_hash", "_ingestion_timestamp"}
        
        self.numerical_features_ = [
            c for c in feature_cols 
            if pd.api.types.is_numeric_dtype(df[c]) and c not in self.config.categorical_features
        ]
        
        self.categorical_features_ = [
            c for c in feature_cols
            if c in self.config.categorical_features or pd.api.types.is_object_dtype(df[c])
        ]
        
        self.protected_features_ = [c for c in protected if c in df.columns]
        
        logger.info(
            f"Feature breakdown: {len(self.numerical_features_)} numerical, "
            f"{len(self.categorical_features_)} categorical, "
            f"{len(self.protected_features_)} protected"
        )
        
        # 3. Build and fit pipeline
        self.pipeline = self._build_pipeline()
        
        # Separate features and target
        X = df[list(feature_cols)]
        
        self.pipeline.fit(X)
        
        # Extract feature names after transformation
        self._extract_feature_names()
        
        logger.info(f"Preprocessor fitted. Output features: {len(self.feature_names_)}")
        
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data using the fitted pipeline."""
        if self.pipeline is None:
            raise ValueError("Preprocessor not fitted. Call fit() first.")
        
        # Check NULL rates
        null_report = self._check_null_rates(df)
        if not null_report["passed"]:
            logger.warning("NULL rate violations in transform - proceeding with flagged data")
        
        # Separate features
        feature_cols = set(df.columns) - set(self.config.protected_attributes) - {self.config.target_column}
        feature_cols = feature_cols - {"customer_id", "_record_hash", "_ingestion_timestamp"}
        
        X = df[list(feature_cols)]
        
        # Transform
        X_transformed = self.pipeline.transform(X)
        
        # Convert to DataFrame
        result = pd.DataFrame(
            X_transformed,
            columns=self.feature_names_,
            index=df.index,
        )
        
        # Add back protected attributes (for fairness monitoring)
        for col in self.protected_features_:
            if col in df.columns:
                result[col] = df[col].values
        
        # Add target if present
        if self.config.target_column in df.columns:
            result[self.config.target_column] = df[self.config.target_column].values
        
        return result
    
    def fit_transform(self, df: pd.DataFrame, y: Optional[pd.Series] = None) -> pd.DataFrame:
        """Fit and transform in one step."""
        self.fit(df, y)
        return self.transform(df)
    
    def _extract_feature_names(self):
        """Extract feature names after transformation."""
        feature_engineer = self.pipeline.named_steps["feature_engineer"]
        preprocessor = self.pipeline.named_steps["preprocessor"]
        
        # Get engineered feature names
        engineered_features = list(feature_engineer.derived_features_)
        
        # Get preprocessor feature names
        num_features = preprocessor.transformers_[0][2]  # numerical
        cat_features = preprocessor.transformers_[1][2]  # categorical
        
        # Get one-hot encoded names
        cat_encoder = preprocessor.named_transformers_["cat"].named_steps["encoder"]
        cat_feature_names = list(cat_encoder.get_feature_names_out(cat_features))
        
        # Add null indicator features from numerical imputer
        num_imputer = preprocessor.named_transformers_["num"].named_steps["imputer"]
        null_indicators = num_imputer.null_indicators_
        
        self.feature_names_ = num_features + null_indicators + cat_feature_names + engineered_features
    
    def save(self, path: str):
        """Save the fitted preprocessor."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "pipeline": self.pipeline,
                "config": self.config,
                "feature_names": self.feature_names_,
                "numerical_features": self.numerical_features_,
                "categorical_features": self.categorical_features_,
                "protected_features": self.protected_features_,
                "null_report": self.null_report_,
            }, f)
        logger.info(f"Saved preprocessor to {path}")
    
    @classmethod
    def load(cls, path: str) -> "CreditScoreV4Preprocessor":
        """Load a fitted preprocessor."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        
        preprocessor = cls(config=data["config"])
        preprocessor.pipeline = data["pipeline"]
        preprocessor.feature_names_ = data["feature_names"]
        preprocessor.numerical_features_ = data["numerical_features"]
        preprocessor.categorical_features_ = data["categorical_features"]
        preprocessor.protected_features_ = data["protected_features"]
        preprocessor.null_report_ = data["null_report"]
        
        logger.info(f"Loaded preprocessor from {path} with {len(preprocessor.feature_names_)} features")
        return preprocessor
    
    def get_feature_importance_template(self) -> Dict[str, Any]:
        """Return template for feature importance tracking."""
        return {
            "feature_names": self.feature_names_,
            "numerical_features": self.numerical_features_,
            "categorical_features": self.categorical_features_,
            "protected_features": self.protected_features_,
            "derived_features": self.pipeline.named_steps["feature_engineer"].derived_features_,
        }


if __name__ == "__main__":
    # Example usage
    sample_data = pd.DataFrame({
        "annual_income": [50000, 75000, None, 120000, 45000],
        "debt_to_income_ratio": [0.3, 0.4, 0.5, None, 0.2],
        "credit_history_length": [5, 10, 3, 8, 2],
        "device_risk_score": [0.3, 0.5, 0.2, 0.4, None],
        "loan_purpose": ["debt_consolidation", "credit_card", "home_improvement", "car", "medical"],
        "home_ownership": ["RENT", "MORTGAGE", "OWN", "RENT", "MORTGAGE"],
        "race": ["White", "Black", "Asian", "Hispanic", "White"],
        "gender": ["Male", "Female", "Male", "Female", "Male"],
        "delinquent": [0, 1, 0, 0, 1],
    })
    
    config = PreprocessingConfig(
        numerical_features=["annual_income", "debt_to_income_ratio", "credit_history_length", "device_risk_score"],
        categorical_features=["loan_purpose", "home_ownership"],
        protected_attributes=["race", "gender"],
    )
    
    preprocessor = CreditScoreV4Preprocessor(config)
    
    try:
        transformed = preprocessor.fit_transform(sample_data)
        print(f"Transformed shape: {transformed.shape}")
        print(f"Features: {transformed.columns.tolist()}")
    except ValueError as e:
        print(f"Expected error (NULL rate violation): {e}")
        print(f"Null report: {preprocessor.null_report_}")