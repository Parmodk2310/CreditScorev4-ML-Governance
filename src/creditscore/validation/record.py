"""Single-record validation against the shared credit-application contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any

from .contract import DataContract


@dataclass(frozen=True)
class RecordContractViolation:
    """One online scoring-record contract violation."""

    rule_id: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"rule_id": self.rule_id, "message": self.message}


class RecordContractValidator:
    """Apply row-level portions of the batch data contract to online requests.

    Batch-only rules such as minimum row count, uniqueness across a dataset, and
    aggregate null-rate thresholds are intentionally left to DataContractValidator.
    A null value is allowed online only when the shared contract allows some
    missingness for that field.
    """

    def __init__(self, contract: DataContract):
        self.contract = contract

    def validate(self, record: Mapping[str, Any]) -> list[RecordContractViolation]:
        violations: list[RecordContractViolation] = []

        for column in self.contract.required_columns:
            if column not in record:
                violations.append(
                    RecordContractViolation(
                        rule_id=f"{column}.required",
                        message=f"{column} is required by the scoring contract.",
                    )
                )

        if not self.contract.allow_extra_columns:
            for column in sorted(set(record) - set(self.contract.columns)):
                violations.append(
                    RecordContractViolation(
                        rule_id=f"{column}.unexpected",
                        message=f"{column} is not allowed by this contract version.",
                    )
                )

        for column, spec in self.contract.columns.items():
            if column not in record:
                continue

            value = record[column]
            max_null_rate = spec.get("max_null_rate")
            if value is None:
                if max_null_rate is None or float(max_null_rate) <= 0.0:
                    violations.append(
                        RecordContractViolation(
                            rule_id=f"{column}.null",
                            message=f"{column} cannot be null under this contract.",
                        )
                    )
                continue

            expected_type = str(spec.get("type", ""))
            if expected_type and not self._matches_type(value, expected_type):
                violations.append(
                    RecordContractViolation(
                        rule_id=f"{column}.type",
                        message=f"{column} must preserve contracted type {expected_type}.",
                    )
                )
                continue

            if isinstance(value, Real) and not isinstance(value, bool):
                minimum = spec.get("min")
                maximum = spec.get("max")
                if minimum is not None and value < minimum:
                    violations.append(
                        RecordContractViolation(
                            rule_id=f"{column}.range",
                            message=f"{column} is below the contracted minimum.",
                        )
                    )
                if maximum is not None and value > maximum:
                    violations.append(
                        RecordContractViolation(
                            rule_id=f"{column}.range",
                            message=f"{column} is above the contracted maximum.",
                        )
                    )

            if "allowed_values" in spec:
                allowed = {str(item) for item in spec["allowed_values"]}
                if str(value) not in allowed:
                    violations.append(
                        RecordContractViolation(
                            rule_id=f"{column}.allowed_values",
                            message=f"{column} is not an allowed category for this contract.",
                        )
                    )

        return violations

    @staticmethod
    def _matches_type(value: Any, expected_type: str) -> bool:
        if expected_type == "integer":
            return isinstance(value, Integral) and not isinstance(value, bool)
        if expected_type == "number":
            return isinstance(value, Real) and not isinstance(value, bool)
        if expected_type == "string":
            return isinstance(value, str)
        return False
