"""
Schema Drift Detection and Data Contract Validation.
Detects upstream schema changes that could silently break the pipeline.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from loguru import logger


class SchemaDriftDetector:
    """
    Detects schema drift by comparing current schema against a baseline.
    
    This catches the type of incident where upstream vendor migrations
    change column names, add/remove columns, or alter data types silently.
    """
    
    def __init__(self, baseline_schema_path: Optional[str] = None):
        self.baseline_schema_path = baseline_schema_path or "data/validation/baseline_schema.json"
        self.baseline_schema: Optional[Dict[str, Any]] = None
        
        if Path(self.baseline_schema_path).exists():
            with open(self.baseline_schema_path, "r") as f:
                self.baseline_schema = json.load(f)
            logger.info(f"Loaded baseline schema from {self.baseline_schema_path}")
    
    def extract_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract schema information from a DataFrame."""
        schema = {
            "columns": {},
            "column_order": list(df.columns),
            "total_columns": len(df.columns),
            "row_count": len(df),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "schema_hash": self._compute_schema_hash(df),
        }
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema["columns"][col] = {
                "dtype": dtype,
                "nullable": df[col].isnull().any(),
                "null_rate": float(df[col].isnull().mean()),
                "unique_count": int(df[col].nunique()),
                "sample_values": self._get_sample_values(df[col]),
            }
            
            # Add type-specific stats
            if pd.api.types.is_numeric_dtype(df[col]):
                schema["columns"][col].update({
                    "min": float(df[col].min()) if not df[col].isnull().all() else None,
                    "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                })
            elif pd.api.types.is_string_dtype(df[col]):
                schema["columns"][col].update({
                    "max_length": int(df[col].astype(str).str.len().max()),
                    "min_length": int(df[col].astype(str).str.len().min()),
                })
        
        return schema
    
    def _compute_schema_hash(self, df: pd.DataFrame) -> str:
        """Compute a hash of the schema for quick comparison."""
        schema_info = {
            "columns": sorted(df.columns.tolist()),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
        }
        schema_str = json.dumps(schema_info, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()[:16]
    
    def _get_sample_values(self, series: pd.Series, n: int = 5) -> List[Any]:
        """Get non-null sample values from a series."""
        non_null = series.dropna().head(n)
        return [self._serialize_value(v) for v in non_null.tolist()]
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for JSON compatibility."""
        if pd.isna(value):
            return None
        if isinstance(value, (pd.Timestamp, datetime)):
            return value.isoformat()
        if isinstance(value, (int, float, str, bool, type(None))):
            return value
        return str(value)
    
    def detect_drift(
        self,
        df: pd.DataFrame,
        strict_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Detect schema drift between current data and baseline.
        
        Args:
            df: Current DataFrame to check
            strict_mode: If True, any schema change is a violation
            
        Returns:
            Drift detection results
        """
        current_schema = self.extract_schema(df)
        
        if self.baseline_schema is None:
            logger.warning("No baseline schema found, saving current as baseline")
            self.save_baseline(current_schema)
            return {
                "drift_detected": False,
                "message": "No baseline schema - saved current as baseline",
                "violations": [],
            }
        
        violations: List[Dict[str, Any]] = []
        
        # Check 1: Column additions
        baseline_cols = set(self.baseline_schema["columns"].keys())
        current_cols = set(current_schema["columns"].keys())
        
        added_cols = current_cols - baseline_cols
        if added_cols:
            violations.append({
                "type": "columns_added",
                "severity": "warning" if not strict_mode else "error",
                "columns": list(added_cols),
                "message": f"New columns detected: {added_cols}",
            })
        
        # Check 2: Column removals (CRITICAL)
        removed_cols = baseline_cols - current_cols
        if removed_cols:
            violations.append({
                "type": "columns_removed",
                "severity": "critical",
                "columns": list(removed_cols),
                "message": f"Columns missing: {removed_cols} - THIS IS THE INCIDENT PATTERN",
            })
        
        # Check 3: Data type changes
        common_cols = baseline_cols & current_cols
        for col in common_cols:
            baseline_dtype = self.baseline_schema["columns"][col]["dtype"]
            current_dtype = current_schema["columns"][col]["dtype"]
            
            if baseline_dtype != current_dtype:
                violations.append({
                    "type": "dtype_changed",
                    "severity": "critical",
                    "column": col,
                    "expected": baseline_dtype,
                    "actual": current_dtype,
                    "message": f"Column '{col}' changed from {baseline_dtype} to {current_dtype}",
                })
        
        # Check 4: NULL rate changes (THE KEY INCIDENT DETECTION)
        for col in common_cols:
            baseline_null = self.baseline_schema["columns"][col].get("null_rate", 0)
            current_null = current_schema["columns"][col].get("null_rate", 0)
            
            null_increase = current_null - baseline_null
            if null_increase > 0.05:  # 5% increase threshold
                violations.append({
                    "type": "null_rate_increase",
                    "severity": "critical",
                    "column": col,
                    "baseline_null_rate": baseline_null,
                    "current_null_rate": current_null,
                    "increase": null_increase,
                    "message": (
                        f"NULL rate for '{col}' increased from {baseline_null:.1%} "
                        f"to {current_null:.1%} (+{null_increase:.1%}) - "
                        f"INCIDENT PATTERN DETECTED"
                    ),
                })
        
        # Check 5: Schema hash comparison
        if self.baseline_schema.get("schema_hash") != current_schema["schema_hash"]:
            violations.append({
                "type": "schema_hash_mismatch",
                "severity": "warning",
                "message": "Schema hash mismatch detected",
                "baseline_hash": self.baseline_schema.get("schema_hash"),
                "current_hash": current_schema["schema_hash"],
            })
        
        drift_detected = len(violations) > 0
        critical_violations = [v for v in violations if v["severity"] == "critical"]
        
        result = {
            "drift_detected": drift_detected,
            "critical_violations": len(critical_violations),
            "total_violations": len(violations),
            "violations": violations,
            "baseline_schema_hash": self.baseline_schema.get("schema_hash"),
            "current_schema_hash": current_schema["schema_hash"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if drift_detected:
            logger.warning(
                f"Schema drift detected: {len(violations)} violations, "
                f"{len(critical_violations)} critical"
            )
            for v in critical_violations:
                logger.critical(f"CRITICAL: {v['message']}")
        else:
            logger.info("No schema drift detected")
        
        return result
    
    def save_baseline(self, schema: Optional[Dict[str, Any]] = None):
        """Save current or provided schema as the new baseline."""
        schema = schema or self.baseline_schema
        if schema is None:
            raise ValueError("No schema to save as baseline")
        
        Path(self.baseline_schema_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_schema_path, "w") as f:
            json.dump(schema, f, indent=2, default=str)
        
        self.baseline_schema = schema
        logger.info(f"Saved baseline schema to {self.baseline_schema_path}")
    
    def update_baseline_from_dataframe(self, df: pd.DataFrame):
        """Extract schema from DataFrame and save as baseline."""
        schema = self.extract_schema(df)
        self.save_baseline(schema)


class DataContractValidator:
    """
    Validates data against explicit data contracts.
    Contracts define expected structure, types, and constraints.
    """
    
    def __init__(self, contracts_path: Optional[str] = None):
        self.contracts_path = contracts_path or "configs/data_contracts"
        self.contracts: Dict[str, Dict[str, Any]] = {}
        self._load_contracts()
    
    def _load_contracts(self):
        """Load data contracts from configuration."""
        # Default contracts (can be overridden by files)
        self.contracts["ingestion_contract"] = {
            "description": "Validates raw data from upstream vendor",
            "required_columns": [
                "customer_id", "annual_income", "debt_to_income_ratio",
                "credit_history_length", "device_risk_score", "loan_purpose",
                "home_ownership", "verification_status", "delinquent",
            ],
            "column_types": {
                "customer_id": "string",
                "annual_income": "numeric",
                "debt_to_income_ratio": "numeric",
                "credit_history_length": "numeric",
                "device_risk_score": "numeric",
                "loan_purpose": "categorical",
                "home_ownership": "categorical",
                "verification_status": "categorical",
                "delinquent": "binary",
            },
            "constraints": {
                "annual_income": {"min": 0, "max": 5000000},
                "debt_to_income_ratio": {"min": 0, "max": 1},
                "device_risk_score": {"min": 0, "max": 1},
                "credit_history_length": {"min": 0, "max": 50},
                "delinquent": {"allowed": [0, 1]},
            },
        }
        
        self.contracts["preprocessing_contract"] = {
            "description": "Validates data after preprocessing",
            "required_columns": [
                "customer_id", "annual_income", "debt_to_income_ratio",
                "credit_history_length", "device_risk_score", "loan_purpose_encoded",
                "home_ownership_encoded", "verification_status_encoded", "delinquent",
            ],
            "no_nulls": True,
            "no_leakage": True,
        }
    
    def validate_contract(
        self,
        df: pd.DataFrame,
        contract_name: str,
    ) -> Dict[str, Any]:
        """
        Validate a DataFrame against a named contract.
        
        Returns:
            Validation results with pass/fail status and details.
        """
        if contract_name not in self.contracts:
            raise ValueError(f"Unknown contract: {contract_name}")
        
        contract = self.contracts[contract_name]
        violations = []
        
        # Check required columns
        if "required_columns" in contract:
            missing = set(contract["required_columns"]) - set(df.columns)
            if missing:
                violations.append({
                    "type": "missing_columns",
                    "severity": "critical",
                    "columns": list(missing),
                    "message": f"Missing required columns: {missing}",
                })
        
        # Check column types
        if "column_types" in contract:
            for col, expected_type in contract["column_types"].items():
                if col not in df.columns:
                    continue
                
                actual_type = self._get_type_category(df[col])
                if actual_type != expected_type:
                    violations.append({
                        "type": "type_mismatch",
                        "severity": "error",
                        "column": col,
                        "expected": expected_type,
                        "actual": actual_type,
                    })
        
        # Check constraints
        if "constraints" in contract:
            for col, constraint in contract["constraints"].items():
                if col not in df.columns:
                    continue
                
                if "min" in constraint or "max" in constraint:
                    col_min = df[col].min()
                    col_max = df[col].max()
                    
                    if "min" in constraint and col_min < constraint["min"]:
                        violations.append({
                            "type": "constraint_violation",
                            "severity": "error",
                            "column": col,
                            "constraint": f"min >= {constraint['min']}",
                            "actual_min": col_min,
                        })
                    
                    if "max" in constraint and col_max > constraint["max"]:
                        violations.append({
                            "type": "constraint_violation",
                            "severity": "error",
                            "column": col,
                            "constraint": f"max <= {constraint['max']}",
                            "actual_max": col_max,
                        })
                
                if "allowed" in constraint:
                    invalid = set(df[col].dropna().unique()) - set(constraint["allowed"])
                    if invalid:
                        violations.append({
                            "type": "invalid_values",
                            "severity": "error",
                            "column": col,
                            "allowed": constraint["allowed"],
                            "invalid_values": list(invalid),
                        })
        
        # Check no nulls
        if contract.get("no_nulls", False):
            null_counts = df.isnull().sum()
            cols_with_nulls = null_counts[null_counts > 0]
            if not cols_with_nulls.empty:
                violations.append({
                    "type": "null_values_present",
                    "severity": "critical",
                    "columns": cols_with_nulls.to_dict(),
                    "message": f"NULL values found in {len(cols_with_nulls)} columns",
                })
        
        passed = len([v for v in violations if v["severity"] == "critical"]) == 0
        
        return {
            "contract_name": contract_name,
            "passed": passed and len(violations) == 0,
            "critical_violations": len([v for v in violations if v["severity"] == "critical"]),
            "total_violations": len(violations),
            "violations": violations,
        }
    
    def _get_type_category(self, series: pd.Series) -> str:
        """Categorize a pandas Series into a type category."""
        if pd.api.types.is_bool_dtype(series):
            return "binary"
        elif pd.api.types.is_integer_dtype(series):
            if series.nunique() <= 2:
                return "binary"
            return "numeric"
        elif pd.api.types.is_float_dtype(series):
            return "numeric"
        elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            if series.nunique() <= 20:
                return "categorical"
            return "string"
        return "unknown"


if __name__ == "__main__":
    # Example usage
    detector = SchemaDriftDetector()
    
    # Simulate creating baseline
    sample_df = pd.DataFrame({
        "device_risk_score": [0.3, 0.5, 0.2, None, 0.4],
        "annual_income": [50000, 75000, 120000, 45000, 90000],
        "delinquent": [0, 1, 0, 0, 1],
    })
    
    detector.update_baseline_from_dataframe(sample_df)
    
    # Simulate incident data (22% NULL in device_risk_score)
    incident_df = pd.DataFrame({
        "device_risk_score": [None] * 22 + [0.3] * 78,
        "annual_income": [50000] * 100,
        "delinquent": [0] * 100,
    })
    
    result = detector.detect_drift(incident_df)
    print(json.dumps(result, indent=2, default=str))