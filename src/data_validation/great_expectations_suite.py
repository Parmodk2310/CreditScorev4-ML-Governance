"""
Great Expectations Suite for CreditScoreV4 Data Quality Gates.
Implements the key fix for the 22% → <1% NULL rate issue.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import great_expectations as gx
import pandas as pd
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations.core import (
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToBeBetween,
    ExpectColumnValuesToBeInSet,
    ExpectColumnDistinctValuesToBeInSet,
    ExpectColumnMeanToBeBetween,
    ExpectColumnStdToBeBetween,
    ExpectColumnPairValuesToBeEqual,
)
from loguru import logger


class CreditScoreV4ValidationSuite:
    """
    Comprehensive data validation suite for CreditScoreV4.
    
    This suite was designed specifically to prevent the incident where
    an upstream vendor migration caused a 22% NULL rate in device_risk_score,
    leading to silent median imputation and approval rate inflation.
    """
    
    SUITE_NAME = "creditscorev4_suite"
    CHECKPOINT_NAME = "creditscorev4_checkpoint"
    
    # NULL thresholds - THE KEY FIX
    NULL_THRESHOLDS = {
        "global": 0.05,           # 5% max NULL rate globally
        "device_risk_score": 0.02,  # Was 22% during incident → now <1%
        "annual_income": 0.01,
        "debt_to_income_ratio": 0.03,
        "credit_history_length": 0.03,
        "employment_length": 0.05,
        "num_credit_lines": 0.02,
        "avg_credit_utilization": 0.03,
        "loan_purpose": 0.01,
        "home_ownership": 0.01,
        "verification_status": 0.01,
        "state": 0.01,
        "race": 0.01,
        "gender": 0.01,
        "age_group": 0.01,
        "delinquent": 0.00,  # Target must never be NULL
    }
    
    # Expected ranges for numerical features
    NUMERICAL_RANGES = {
        "credit_history_length": {"min": 0, "max": 50},
        "debt_to_income_ratio": {"min": 0.0, "max": 1.0},
        "annual_income": {"min": 0, "max": 5000000},
        "device_risk_score": {"min": 0.0, "max": 1.0},
        "employment_length": {"min": 0, "max": 50},
        "num_credit_lines": {"min": 0, "max": 50},
        "avg_credit_utilization": {"min": 0.0, "max": 1.0},
    }
    
    # Expected categorical values
    CATEGORICAL_VALUES = {
        "loan_purpose": ["debt_consolidation", "credit_card", "home_improvement", 
                         "major_purchase", "small_business", "car", "medical", "moving",
                         "vacation", "house", "wedding", "renewable_energy", "other"],
        "home_ownership": ["RENT", "MORTGAGE", "OWN", "ANY", "OTHER", "NONE"],
        "verification_status": ["Verified", "Source Verified", "Not Verified"],
        "race": ["White", "Black", "Asian", "Hispanic", "Other", "Native American", 
                 "Pacific Islander"],
        "gender": ["Male", "Female", "Non-Binary", "Prefer not to say"],
        "age_group": ["18-25", "26-35", "36-45", "46-55", "55+"],
    }
    
    def __init__(self, context_root_dir: Optional[str] = None):
        """
        Initialize the validation suite.
        
        Args:
            context_root_dir: Path to Great Expectations context directory.
        """
        self.context_root_dir = context_root_dir or "great_expectations"
        
        try:
            self.context = gx.get_context(
                context_root_dir=self.context_root_dir,
                runtime_environment={"plugins_directory": f"{self.context_root_dir}/plugins"},
            )
        except Exception:
            # Create new context if it doesn't exist
            self.context = gx.get_context(
                context_root_dir=self.context_root_dir,
            )
        
        logger.info(f"Initialized Great Expectations context at {self.context_root_dir}")
    
    def create_or_update_suite(self) -> ExpectationSuite:
        """Create or update the CreditScoreV4 expectation suite."""
        try:
            suite = self.context.get_expectation_suite(self.SUITE_NAME)
            logger.info(f"Loaded existing suite: {self.SUITE_NAME}")
        except Exception:
            suite = self.context.create_expectation_suite(
                expectation_suite_name=self.SUITE_NAME,
                overwrite_existing=True,
            )
            logger.info(f"Created new suite: {self.SUITE_NAME}")
        
        # Clear existing expectations
        suite.expectations = []
        
        # 1. Table-level expectations
        suite.add_expectation(
            ExpectTableRowCountToBeBetween(
                min_value=1000,
                max_value=10000000,
                meta={"description": "Ensure table has reasonable row count"},
            )
        )
        
        # 2. NULL threshold expectations - THE KEY FIX
        for column, threshold in self.NULL_THRESHOLDS.items():
            if threshold == 0.00:
                # Strict no-NULL for critical columns
                suite.add_expectation(
                    ExpectColumnValuesToNotBeNull(
                        column=column,
                        mostly=1.0,
                        meta={
                            "description": f"Critical column {column} must have no NULLs",
                            "incident_reference": "INC-2024-001",
                        },
                    )
                )
            else:
                suite.add_expectation(
                    ExpectColumnValuesToNotBeNull(
                        column=column,
                        mostly=1.0 - threshold,
                        meta={
                            "description": f"Column {column} NULL rate must be below {threshold*100}%",
                            "threshold": threshold,
                            "incident_reference": "INC-2024-001",
                        },
                    )
                )
        
        # 3. Numerical range expectations
        for column, ranges in self.NUMERICAL_RANGES.items():
            suite.add_expectation(
                ExpectColumnValuesToBeBetween(
                    column=column,
                    min_value=ranges["min"],
                    max_value=ranges["max"],
                    mostly=0.99,
                    meta={
                        "description": f"{column} must be within valid range",
                        "valid_range": ranges,
                    },
                )
            )
        
        # 4. Categorical value expectations
        for column, values in self.CATEGORICAL_VALUES.items():
            suite.add_expectation(
                ExpectColumnDistinctValuesToBeInSet(
                    column=column,
                    value_set=values,
                    meta={
                        "description": f"{column} must contain only known values",
                        "allowed_values": values,
                    },
                )
            )
        
        # 5. Target variable expectation
        suite.add_expectation(
            ExpectColumnValuesToBeInSet(
                column="delinquent",
                value_set=[0, 1],
                meta={"description": "Target must be binary (0 or 1)"},
            )
        )
        
        # 6. Distribution expectations (for key features)
        suite.add_expectation(
            ExpectColumnMeanToBeBetween(
                column="device_risk_score",
                min_value=0.20,
                max_value=0.60,
                meta={
                    "description": "device_risk_score mean should be stable",
                    "incident_reference": "INC-2024-001",
                    "historical_mean": 0.31,
                    "incident_mean": 0.44,
                },
            )
        )
        
        suite.add_expectation(
            ExpectColumnStdToBeBetween(
                column="device_risk_score",
                min_value=0.10,
                max_value=0.30,
                meta={"description": "device_risk_score std should be stable"},
            )
        )
        
        # Save the suite
        self.context.save_expectation_suite(suite)
        logger.info(f"Saved suite with {len(suite.expectations)} expectations")
        
        return suite
    
    def validate_dataframe(
        self,
        df: pd.DataFrame,
        batch_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a pandas DataFrame against the CreditScoreV4 suite.
        
        Args:
            df: DataFrame to validate
            batch_kwargs: Optional batch configuration
            
        Returns:
            Validation results dictionary
        """
        suite = self.create_or_update_suite()
        
        # Create batch request
        batch_request = RuntimeBatchRequest(
            datasource_name="pandas_datasource",
            data_asset_name="creditscorev4_batch",
            runtime_parameters={"batch_data": df},
            batch_identifiers={
                "timestamp": pd.Timestamp.now().isoformat(),
                "row_count": str(len(df)),
            },
        )
        
        # Create checkpoint
        checkpoint_config = {
            "name": self.CHECKPOINT_NAME,
            "config_version": 1.0,
            "class_name": "SimpleCheckpoint",
            "run_name_template": "%Y%m%d-%H%M%S",
            "validations": [
                {
                    "batch_request": batch_request,
                    "expectation_suite_name": self.SUITE_NAME,
                }
            ],
        }
        
        checkpoint = self.context.add_or_update_checkpoint(**checkpoint_config)
        
        # Run validation
        checkpoint_result = checkpoint.run()
        
        # Extract results
        results = self._parse_checkpoint_results(checkpoint_result)
        
        logger.info(
            f"Validation complete: {results['success_rate']:.1%} pass rate, "
            f"{results['failed_expectations']} failed expectations"
        )
        
        return results
    
    def _parse_checkpoint_results(self, checkpoint_result) -> Dict[str, Any]:
        """Parse checkpoint results into a structured dictionary."""
        validation_results = checkpoint_result.list_validation_results()
        
        if not validation_results:
            return {
                "success": False,
                "success_rate": 0.0,
                "total_expectations": 0,
                "failed_expectations": 0,
                "details": [],
            }
        
        result = validation_results[0]
        statistics = result.statistics
        
        details = []
        for expectation_result in result.results:
            expectation = expectation_result.expectation_config
            result_info = expectation_result.result
            
            detail = {
                "expectation_type": expectation.expectation_type,
                "column": expectation.kwargs.get("column", "N/A"),
                "success": expectation_result.success,
                "kwargs": {k: v for k, v in expectation.kwargs.items() if k != "result_format"},
            }
            
            if not expectation_result.success:
                detail["unexpected_count"] = result_info.get("unexpected_count", "N/A")
                detail["unexpected_percent"] = result_info.get("unexpected_percent", "N/A")
                detail["partial_unexpected_list"] = result_info.get("partial_unexpected_list", [])
            
            details.append(detail)
        
        return {
            "success": statistics["success_percent"] == 100.0,
            "success_rate": statistics["success_percent"] / 100.0,
            "total_expectations": statistics["evaluated_expectations"],
            "failed_expectations": statistics["unsuccessful_expectations"],
            "details": details,
        }
    
    def generate_data_quality_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable data quality report."""
        lines = [
            "=" * 60,
            "CREDITSCOREV4 DATA QUALITY REPORT",
            "=" * 60,
            f"Success Rate: {results['success_rate']:.1%}",
            f"Total Expectations: {results['total_expectations']}",
            f"Failed Expectations: {results['failed_expectations']}",
            "-" * 60,
        ]
        
        if results['failed_expectations'] > 0:
            lines.append("\\n❌ FAILED EXPECTATIONS:")
            for detail in results['details']:
                if not detail['success']:
                    lines.append(f"  • {detail['expectation_type']} on '{detail['column']}'")
                    if 'unexpected_percent' in detail:
                        lines.append(f"    Unexpected: {detail['unexpected_percent']:.2f}%")
        
        lines.append("\\n✅ PASSED EXPECTATIONS:")
        passed = [d for d in results['details'] if d['success']]
        for detail in passed[:5]:  # Show first 5
            lines.append(f"  • {detail['expectation_type']} on '{detail['column']}'")
        if len(passed) > 5:
            lines.append(f"  ... and {len(passed) - 5} more")
        
        lines.append("=" * 60)
        
        return "\\n".join(lines)


class NullRateMonitor:
    """
    Dedicated monitor for NULL rate tracking.
    This was the primary detection mechanism that would have caught the incident.
    """
    
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or CreditScoreV4ValidationSuite.NULL_THRESHOLDS
        self.violations: List[Dict[str, Any]] = []
    
    def check_null_rates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check NULL rates for all columns against thresholds.
        
        Returns:
            Dictionary with violation details.
        """
        null_rates = df.isnull().mean()
        self.violations = []
        
        for column, threshold in self.thresholds.items():
            if column not in null_rates:
                continue
            
            actual_rate = null_rates[column]
            if actual_rate > threshold:
                self.violations.append({
                    "column": column,
                    "actual_rate": actual_rate,
                    "threshold": threshold,
                    "excess": actual_rate - threshold,
                    "severity": "critical" if actual_rate > threshold * 2 else "warning",
                })
        
        return {
            "total_violations": len(self.violations),
            "violations": self.violations,
            "null_rates": null_rates.to_dict(),
            "passed": len(self.violations) == 0,
        }
    
    def get_violations(self) -> List[Dict[str, Any]]:
        """Return list of current violations."""
        return self.violations


if __name__ == "__main__":
    # Example: Create suite
    suite_manager = CreditScoreV4ValidationSuite()
    suite = suite_manager.create_or_update_suite()
    print(f"Created suite with {len(suite.expectations)} expectations")
