"""Domain-level data contract validation independent of a vendor tool."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandas.api.types import is_integer_dtype, is_numeric_dtype, is_string_dtype

from .contract import DataContract
from .models import DataQualityReport, RuleResult


class DataContractValidator:
    """Validate schema, missingness, uniqueness, ranges, and categories."""

    def __init__(self, contract: DataContract):
        self.contract = contract

    def validate(self, frame: pd.DataFrame, *, batch_name: str, source: str) -> DataQualityReport:
        rules: list[RuleResult] = []

        rules.append(
            self._rule(
                "table.minimum_rows",
                len(frame) >= self.contract.minimum_rows,
                len(frame),
                f">= {self.contract.minimum_rows}",
                "Batch must contain enough records to be evaluated safely.",
            )
        )

        missing = sorted(set(self.contract.required_columns) - set(frame.columns))
        rules.append(
            self._rule(
                "schema.required_columns",
                not missing,
                missing,
                "no required columns missing",
                "Required scoring columns must be present.",
            )
        )

        if not self.contract.allow_extra_columns:
            extra = sorted(set(frame.columns) - set(self.contract.columns))
            rules.append(
                self._rule(
                    "schema.extra_columns",
                    not extra,
                    extra,
                    "no unexpected columns",
                    "Unexpected columns are blocked by this contract version.",
                )
            )

        for column, spec in self.contract.columns.items():
            if column not in frame.columns:
                continue
            series = frame[column]
            expected_type = str(spec.get("type", ""))
            if expected_type:
                rules.append(self._validate_type(column, series, expected_type))

            max_null_rate = spec.get("max_null_rate")
            if max_null_rate is not None:
                observed_null_rate = float(series.isna().mean())
                rules.append(
                    self._rule(
                        f"{column}.null_rate",
                        observed_null_rate <= float(max_null_rate) + 1e-12,
                        round(observed_null_rate, 6),
                        f"<= {float(max_null_rate):.6f}",
                        f"{column} missingness must remain within the contract threshold.",
                    )
                )

            if bool(spec.get("unique", False)):
                duplicate_count = int(series.duplicated(keep=False).sum())
                rules.append(
                    self._rule(
                        f"{column}.unique",
                        duplicate_count == 0,
                        duplicate_count,
                        0,
                        f"{column} must uniquely identify an application.",
                    )
                )

            if "min" in spec or "max" in spec:
                rules.append(self._validate_range(column, series, spec))

            if "allowed_values" in spec:
                allowed = set(spec["allowed_values"])
                observed = set(series.dropna().astype(str).unique())
                unexpected = sorted(observed - allowed)
                rules.append(
                    self._rule(
                        f"{column}.allowed_values",
                        not unexpected,
                        unexpected,
                        sorted(allowed),
                        f"{column} must use the contract's known categories.",
                    )
                )

        return DataQualityReport(
            engine="contract",
            batch_name=batch_name,
            source=source,
            passed=all(rule.passed for rule in rules),
            row_count=len(frame),
            rules=rules,
            metadata={
                "contract_name": self.contract.name,
                "contract_version": self.contract.version,
            },
        )

    @staticmethod
    def _rule(
        rule_id: str,
        passed: bool,
        observed: Any,
        expected: Any,
        detail: str,
    ) -> RuleResult:
        return RuleResult(
            rule_id=rule_id,
            passed=bool(passed),
            severity="critical",
            observed=observed,
            expected=expected,
            detail=detail,
        )

    def _validate_type(self, column: str, series: pd.Series, expected_type: str) -> RuleResult:
        if expected_type == "number":
            passed = is_numeric_dtype(series)
        elif expected_type == "integer":
            passed = is_integer_dtype(series)
        elif expected_type == "string":
            passed = is_string_dtype(series) or series.dtype == object
        else:
            passed = False

        return self._rule(
            f"{column}.type",
            passed,
            str(series.dtype),
            expected_type,
            f"{column} must preserve its contracted logical type.",
        )

    def _validate_range(
        self,
        column: str,
        series: pd.Series,
        spec: dict[str, Any],
    ) -> RuleResult:
        clean = series.dropna()
        minimum = spec.get("min")
        maximum = spec.get("max")
        passed = True
        if minimum is not None:
            passed = passed and bool((clean >= minimum).all())
        if maximum is not None:
            passed = passed and bool((clean <= maximum).all())

        observed: dict[str, Any] = {
            "min": None if clean.empty else float(clean.min()),
            "max": None if clean.empty else float(clean.max()),
        }
        return self._rule(
            f"{column}.range",
            passed,
            observed,
            {"min": minimum, "max": maximum},
            f"{column} values must remain inside the contractual range.",
        )
