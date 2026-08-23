"""
Model Training Pipeline for CreditScoreV4.
Implements XGBoost training with hyperparameter tuning, cross-validation,
and MLflow tracking.
"""

import json
import os
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import mlflow
import mlflow.xgboost
import numpy as np
import pandas as pd
import xgboost as xgb
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, train_test_split


@dataclass
class ModelConfig:
    """Configuration for model training."""
    
    model_type: str = "xgboost"
    
    # XGBoost parameters
    xgboost_params: Dict[str, Any] = field(default_factory=lambda: {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 6,
        "learning_rate": 0.05,
        "n_estimators": 500,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "gamma": 0.1,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
        "n_jobs": -1,
        "early_stopping_rounds": 50,
    })
    
    # Validation
    test_size: float = 0.2
    n_splits: int = 5
    random_state: int = 42
    
    # Thresholds
    min_auc: float = 0.78
    min_precision: float = 0.65
    min_recall: float = 0.70
    
    # MLflow
    experiment_name: str = "creditscorev4_experiment"
    tracking_uri: str = "http://localhost:5000"
    
    # Fairness
    max_fairness_violation: float = 0.05


class ModelMetrics:
    """Compute and store comprehensive model metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, float] = {}
        self.thresholds: Dict[str, float] = {}
        self.confusion_matrix: Optional[np.ndarray] = None
        self.roc_curve: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None
    
    def compute(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        y_pred: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Compute all metrics from predictions."""
        if y_pred is None:
            y_pred = (y_pred_proba >= 0.5).astype(int)
        
        self.metrics = {
            "auc": roc_auc_score(y_true, y_pred_proba),
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1": f1_score(y_true, y_pred, zero_division=0),
            "average_precision": average_precision_score(y_true, y_pred_proba),
        }
        
        self.confusion_matrix = confusion_matrix(y_true, y_pred)
        self.roc_curve = roc_curve(y_true, y_pred_proba)
        
        # Find optimal threshold
        fpr, tpr, thresholds = self.roc_curve
        j_scores = tpr - fpr
        optimal_idx = np.argmax(j_scores)
        self.thresholds["optimal"] = thresholds[optimal_idx]
        self.thresholds["default"] = 0.5
        
        return self.metrics
    
    def get_classification_report(self) -> str:
        """Generate human-readable classification report."""
        lines = [
            "=" * 50,
            "MODEL PERFORMANCE METRICS",
            "=" * 50,
            f"AUC:              {self.metrics.get('auc', 0):.4f}",
            f"Accuracy:         {self.metrics.get('accuracy', 0):.4f}",
            f"Precision:        {self.metrics.get('precision', 0):.4f}",
            f"Recall:           {self.metrics.get('recall', 0):.4f}",
            f"F1-Score:         {self.metrics.get('f1', 0):.4f}",
            f"Avg Precision:    {self.metrics.get('average_precision', 0):.4f}",
            "-" * 50,
            "Confusion Matrix:",
        ]
        
        if self.confusion_matrix is not None:
            cm = self.confusion_matrix
            lines.extend([
                f"                 Predicted",
                f"                 0      1",
                f"Actual    0    {cm[0,0]:5d}  {cm[0,1]:5d}",
                f"          1    {cm[1,0]:5d}  {cm[1,1]:5d}",
            ])
        
        lines.append("=" * 50)
        return "\\n".join(lines)
    
    def meets_thresholds(self, config: ModelConfig) -> Tuple[bool, List[str]]:
        """Check if metrics meet minimum thresholds."""
        failures = []
        
        if self.metrics.get("auc", 0) < config.min_auc:
            failures.append(f"AUC {self.metrics['auc']:.4f} < {config.min_auc}")
        
        if self.metrics.get("precision", 0) < config.min_precision:
            failures.append(f"Precision {self.metrics['precision']:.4f} < {config.min_precision}")
        
        if self.metrics.get("recall", 0) < config.min_recall:
            failures.append(f"Recall {self.metrics['recall']:.4f} < {config.min_recall}")
        
        return len(failures) == 0, failures


class CreditScoreV4Trainer:
    """
    Model trainer for CreditScoreV4 with MLflow integration.
    
    Features:
    - Stratified K-Fold cross-validation
    - Hyperparameter tuning support
    - MLflow experiment tracking
    - Model artifact logging
    - Threshold-based gating
    """
    
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.model: Optional[xgb.XGBClassifier] = None
        self.metrics: Optional[ModelMetrics] = None
        self.cv_results: List[Dict[str, Any]] = []
        self.feature_names: List[str] = []
        self.feature_importance: Optional[pd.DataFrame] = None
        
        # Setup MLflow
        mlflow.set_tracking_uri(self.config.tracking_uri)
        mlflow.set_experiment(self.config.experiment_name)
        
        logger.info(f"Initialized trainer with experiment: {self.config.experiment_name}")
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        feature_columns: Optional[List[str]] = None,
        target_column: str = "delinquent",
    ) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """
        Prepare train/test split.
        
        Args:
            df: Preprocessed DataFrame
            feature_columns: List of feature columns (auto-detected if None)
            target_column: Name of target column
            
        Returns:
            X_train, y_train, X_test, y_test
        """
        # Auto-detect features (exclude protected attributes and metadata)
        if feature_columns is None:
            exclude = {target_column, "race", "gender", "age_group", "customer_id"}
            feature_columns = [c for c in df.columns if c not in exclude]
        
        self.feature_names = feature_columns
        
        X = df[feature_columns]
        y = df[target_column]
        
        # Stratified split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
            stratify=y,
        )
        
        logger.info(
            f"Data split: train={len(X_train)}, test={len(X_test)}, "
            f"positive_rate={y.mean():.3f}"
        )
        
        return X_train, y_train, X_test, y_test
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
    ) -> xgb.XGBClassifier:
        """
        Train the XGBoost model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            
        Returns:
            Trained XGBoost classifier
        """
        logger.info(f"Training XGBoost model on {len(X_train)} samples")
        
        # Calculate scale_pos_weight for imbalanced data
        pos_ratio = y_train.mean()
        scale_pos_weight = (1 - pos_ratio) / pos_ratio if pos_ratio > 0 else 1.0
        
        params = self.config.xgboost_params.copy()
        params["scale_pos_weight"] = scale_pos_weight
        
        # Remove early_stopping_rounds from params (passed to fit instead)
        early_stopping = params.pop("early_stopping_rounds", 50)
        
        self.model = xgb.XGBClassifier(**params)
        
        # Prepare eval set
        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))
        
        # Train with early stopping
        fit_params = {
            "eval_set": eval_set,
            "verbose": False,
        }
        
        if len(eval_set) > 1:
            fit_params["early_stopping_rounds"] = early_stopping
        
        self.model.fit(X_train, y_train, **fit_params)
        
        logger.info(
            f"Training complete. Best iteration: {self.model.best_iteration}, "
            f"Best score: {self.model.best_score:.4f}"
        )
        
        return self.model
    
    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> ModelMetrics:
        """
        Evaluate model on test set.
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            ModelMetrics object
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = self.model.predict(X_test)
        
        self.metrics = ModelMetrics()
        self.metrics.compute(y_test.values, y_pred_proba, y_pred)
        
        # Compute feature importance
        importance = self.model.feature_importances_
        self.feature_importance = pd.DataFrame({
            "feature": self.feature_names,
            "importance": importance,
        }).sort_values("importance", ascending=False)
        
        logger.info(f"Evaluation complete: AUC={self.metrics.metrics['auc']:.4f}")
        logger.info(f"\\n{self.metrics.get_classification_report()}")
        
        return self.metrics
    
    def cross_validate(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> Dict[str, Any]:
        """
        Perform stratified K-Fold cross-validation.
        
        Returns:
            Dictionary with CV results
        """
        logger.info(f"Starting {self.config.n_splits}-fold cross-validation")
        
        skf = StratifiedKFold(
            n_splits=self.config.n_splits,
            shuffle=True,
            random_state=self.config.random_state,
        )
        
        cv_scores = []
        fold_metrics = []
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            logger.info(f"Training fold {fold + 1}/{self.config.n_splits}")
            
            X_train_fold = X.iloc[train_idx]
            y_train_fold = y.iloc[train_idx]
            X_val_fold = X.iloc[val_idx]
            y_val_fold = y.iloc[val_idx]
            
            # Train
            fold_model = xgb.XGBClassifier(**{
                k: v for k, v in self.config.xgboost_params.items() 
                if k != "early_stopping_rounds"
            })
            
            fold_model.fit(
                X_train_fold, y_train_fold,
                eval_set=[(X_val_fold, y_val_fold)],
                early_stopping_rounds=50,
                verbose=False,
            )
            
            # Evaluate
            y_pred_proba = fold_model.predict_proba(X_val_fold)[:, 1]
            fold_auc = roc_auc_score(y_val_fold, y_pred_proba)
            
            cv_scores.append(fold_auc)
            fold_metrics.append({
                "fold": fold + 1,
                "auc": fold_auc,
                "train_size": len(train_idx),
                "val_size": len(val_idx),
            })
        
        self.cv_results = fold_metrics
        
        cv_summary = {
            "mean_auc": float(np.mean(cv_scores)),
            "std_auc": float(np.std(cv_scores)),
            "min_auc": float(np.min(cv_scores)),
            "max_auc": float(np.max(cv_scores)),
            "folds": fold_metrics,
        }
        
        logger.info(
            f"CV complete: {cv_summary['mean_auc']:.4f} (+/- {cv_summary['std_auc']:.4f})"
        )
        
        return cv_summary
    
    def log_to_mlflow(
        self,
        model_name: str = "creditscorev4",
        params: Optional[Dict[str, Any]] = None,
        artifacts: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Log model and metrics to MLflow.
        
        Returns:
            MLflow run ID
        """
        with mlflow.start_run() as run:
            # Log parameters
            if params:
                mlflow.log_params(params)
            mlflow.log_params(self.config.xgboost_params)
            
            # Log metrics
            if self.metrics:
                mlflow.log_metrics(self.metrics.metrics)
            
            # Log CV results
            if self.cv_results:
                cv_summary = self.cross_validate_summary()
                mlflow.log_metrics({
                    "cv_mean_auc": cv_summary["mean_auc"],
                    "cv_std_auc": cv_summary["std_auc"],
                })
            
            # Log feature importance
            if self.feature_importance is not None:
                importance_path = "/tmp/feature_importance.csv"
                self.feature_importance.to_csv(importance_path, index=False)
                mlflow.log_artifact(importance_path, "feature_importance")
            
            # Log model
            if self.model is not None:
                mlflow.xgboost.log_model(
                    self.model,
                    artifact_path="model",
                    registered_model_name=model_name,
                )
            
            # Log additional artifacts
            if artifacts:
                for name, path in artifacts.items():
                    mlflow.log_artifact(path, name)
            
            logger.info(f"Logged to MLflow run: {run.info.run_id}")
            return run.info.run_id
    
    def cross_validate_summary(self) -> Dict[str, float]:
        """Summarize cross-validation results."""
        if not self.cv_results:
            return {}
        
        aucs = [f["auc"] for f in self.cv_results]
        return {
            "mean_auc": float(np.mean(aucs)),
            "std_auc": float(np.std(aucs)),
            "min_auc": float(np.min(aucs)),
            "max_auc": float(np.max(aucs)),
        }
    
    def save_model(self, path: str):
        """Save trained model to disk."""
        if self.model is None:
            raise ValueError("No model to save")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "model": self.model,
            "config": self.config,
            "feature_names": self.feature_names,
            "feature_importance": self.feature_importance,
            "metrics": self.metrics.metrics if self.metrics else {},
            "cv_results": self.cv_results,
        }
        
        with open(path, "wb") as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Saved model to {path}")
    
    @classmethod
    def load_model(cls, path: str) -> Tuple[xgb.XGBClassifier, Dict[str, Any]]:
        """Load trained model from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        
        logger.info(f"Loaded model from {path}")
        return data["model"], data


if __name__ == "__main__":
    # Example usage with synthetic data
    np.random.seed(42)
    n_samples = 10000
    
    synthetic_data = pd.DataFrame({
        "feature_1": np.random.randn(n_samples),
        "feature_2": np.random.randn(n_samples),
        "feature_3": np.random.randn(n_samples),
        "delinquent": np.random.binomial(1, 0.15, n_samples),
    })
    
    trainer = CreditScoreV4Trainer()
    X_train, y_train, X_test, y_test = trainer.prepare_data(synthetic_data)
    
    # Cross-validate
    cv_results = trainer.cross_validate(
        pd.concat([X_train, X_test]),
        pd.concat([y_train, y_test]),
    )
    
    # Train final model
    trainer.train(X_train, y_train, X_test, y_test)
    
    # Evaluate
    metrics = trainer.evaluate(X_test, y_test)
    print(metrics.get_classification_report())