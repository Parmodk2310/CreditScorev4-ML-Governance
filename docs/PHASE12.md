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

## Verified deterministic evidence

The accepted Vendor E fixture measures:

| Signal | Result |
|---|---:|
| Phase 2 data-quality decision | **PASS** |
| Aggregate Phase 3 drift | **STABLE** |
| Target intersection support | **1,058** |
| Reference `female|group_c` | **PASS** |
| Current `female|group_c` | **FAIL** |
| Demographic-parity ratio | **0.7479** |
| Selection-rate difference | **0.1873** |
| Equal-opportunity difference | **0.1956** |
| Equalized-odds difference | **0.2600** |
| False-approval-rate difference | **0.2600** |
| `sex` axis | **PASS** |
| `synthetic_demographic_group` axis | **WARNING** |

Proxy-review priority features:

- `device_risk_score`
- `credit_utilization`
- `bank_transaction_risk`

All configured Phase 12 acceptance gates pass for this deterministic fixture.

## Release integration

The v0.12.0 boundary promotes `make phase12-verify` into CI and the gated
deployment preflight. The scheduled workflow first preserves and verifies the
Phase 11 monitoring contract, then runs Phase 12 analysis/verification and
uploads Phase 12 evidence separately.

The historical Phase 1–7 regression target is frozen to the original Phase 4
fairness tests so later Phase 12 tests do not silently rewrite the historical
63-test boundary.

## Verification

```bash
make phase12-analyze
python scripts/verify_phase12.py
make phase12-test
make phase12-verify
```

Phase 12 remains a deterministic synthetic governance case study.
