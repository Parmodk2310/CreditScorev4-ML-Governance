"""Great Expectations 1.x adapter for the Phase 2 scoring contract."""

from __future__ import annotations

from typing import Any, cast

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd


_gx: Any = cast(Any, gx)
_gxe: Any = cast(Any, gxe)

from .contract import DataContract
from .models import DataQualityReport, RuleResult


def _expectations(contract: DataContract) -> list[Any]:
    expectations: list[Any] = [
        gxe.ExpectTableColumnsToMatchSet(
            column_set=contract.required_columns,
            exact_match=not contract.allow_extra_columns,
        )
    ]

    for column, spec in contract.columns.items():
        max_null_rate = spec.get("max_null_rate")
        if max_null_rate is not None:
            expectations.append(
                gxe.ExpectColumnValuesToNotBeNull(
                    column=column,
                    mostly=1.0 - float(max_null_rate),
                )
            )
        if bool(spec.get("unique", False)):
            expectations.append(gxe.ExpectColumnValuesToBeUnique(column=column))
        if "min" in spec or "max" in spec:
            expectations.append(
                gxe.ExpectColumnValuesToBeBetween(
                    column=column,
                    min_value=spec.get("min"),
                    max_value=spec.get("max"),
                )
            )
        if "allowed_values" in spec:
            expectations.append(
                gxe.ExpectColumnValuesToBeInSet(
                    column=column,
                    value_set=list(spec["allowed_values"]),
                )
            )
    return expectations


def validate_with_gx(
    frame: pd.DataFrame,
    contract: DataContract,
    *,
    batch_name: str,
    source: str,
) -> DataQualityReport:
    """Validate a dataframe using a transient GX context and expectation suite."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="creditscorev4_phase2")
    asset = data_source.add_dataframe_asset(name="credit_applications")
    batch_definition = asset.add_batch_definition_whole_dataframe(name="whole_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": frame})

    suite = gx.ExpectationSuite(name="credit_application_scoring_v1")
    for expectation in _expectations(contract):
        suite.add_expectation(expectation)

    validation = batch.validate(suite)
    payload = validation.to_json_dict()
    rules: list[RuleResult] = []
    for index, result in enumerate(payload.get("results", []), start=1):
        config = result.get("expectation_config", {})
        expectation_type = config.get("type") or config.get("expectation_type") or f"expectation_{index}"
        kwargs = config.get("kwargs", {})
        column = kwargs.get("column")
        rule_id = f"gx.{column}.{expectation_type}" if column else f"gx.{expectation_type}"
        result_payload = result.get("result", {})
        observed = {
            key: result_payload.get(key)
            for key in ("element_count", "unexpected_count", "unexpected_percent", "observed_value")
            if key in result_payload
        }
        rules.append(
            RuleResult(
                rule_id=rule_id,
                passed=bool(result.get("success", False)),
                severity="critical",
                observed=observed,
                expected=kwargs,
                detail="Great Expectations validation result.",
            )
        )

    return DataQualityReport(
        engine="great_expectations",
        batch_name=batch_name,
        source=source,
        passed=bool(payload.get("success", False)),
        row_count=len(frame),
        rules=rules,
        metadata={"gx_version": gx.__version__, "suite": suite.name},
    )
