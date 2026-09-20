# Phase 12 — Intersectional Fairness & Proxy-Risk Evidence

Phase 12 strengthens subgroup governance without changing the trained model or
using protected attributes as model inputs.

## Why this phase exists

Phase 4 proved that aggregate-stable data can still fail a single protected
dimension. Phase 12 tests a harder case: two single protected dimensions can
avoid a blocking `FAIL` while their intersection fails materially.

The deterministic Vendor E fixture stresses non-protected model inputs only for:

```text
sex = female
AND
synthetic_demographic_group = group_c
```

The protected/evaluation columns and `default_30d` labels are preserved.

## Fairness semantics

Phase 12 evaluates the favorable lending decision directly:

```text
approved = risk_probability < 0.50
favorable truth = default_30d == 0
```

Evidence includes:

- demographic-parity ratio;
- selection-rate difference;
- equal-opportunity difference for favorable decisions;
- equalized-odds difference;
- false-approval-rate difference;
- per-group support, approval, default, risk and error-rate evidence.

Only groups meeting the configured minimum support participate in governance
comparisons.

## Proxy-risk screening

Phase 12 separates two questions:

1. is a model input statistically associated with the protected intersection?
2. is that input materially influential in the fitted model?

Numeric association uses eta-squared. Categorical association uses Cramer's V.
Model influence uses SHAP mean absolute attribution.

A feature becomes a **review priority** only when incident-induced association
exceeds the configured project threshold and model influence ranks within the
configured top set.

This is a screening mechanism. Association plus SHAP influence does not prove
causal proxy use, unlawful discrimination, or regulatory non-compliance.

## Intended acceptance story

The release target is a synthetic fixture where:

- Vendor E passes the existing data-quality gate;
- aggregate Phase 3 drift remains STABLE;
- the reference intersection is not a fairness FAIL;
- `sex` alone does not FAIL;
- `synthetic_demographic_group` alone does not FAIL;
- `sex|synthetic_demographic_group` does FAIL;
- the intentionally shifted non-protected features surface in proxy-risk
  evidence;
- protected attributes remain outside the model and SHAP feature spaces.

## Verification

```bash
make phase12-analyze
python scripts/verify_phase12.py
make phase12-test
make phase12-verify
```

Phase 12 remains a deterministic synthetic governance case study.
