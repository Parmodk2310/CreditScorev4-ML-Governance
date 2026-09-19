# Model Card — CreditScoreV4

## Model summary

**Model name:** CreditScoreV4
**Project:** CreditScoreV4 ML Governance
**Purpose:** synthetic credit-risk model governance and controlled release
**Model family:** XGBoost classifier inside a scikit-learn preprocessing pipeline
**Target:** `default_30d`
**Positive class:** `default_30d = 1`
**Primary output:** probability of 30-day default

The system evaluates ML incident detection, evidence-backed governance, and
controlled model release. It is not a real lending system.

## Intended use

Appropriate uses include deterministic ML-governance experiments, data-quality
and drift testing, fairness-monitoring demonstrations, explainability
investigation, promotion-policy testing, safe-release testing, and MLOps/ML
platform engineering review.

Unsupported uses include real credit approval/decline, real applicant risk
assessment, processing real applicant PII, regulatory/legal compliance
decisions, or production banking deployment without substantial additional
validation.

## Model inputs

Raw model inputs from `src/creditscore/data/preprocessing.py`:

- `age`
- `annual_income`
- `employment_length_years`
- `debt_to_income`
- `credit_utilization`
- `credit_history_years`
- `delinquencies_2y`
- `inquiries_6m`
- `open_credit_accounts`
- `device_risk_score`
- `bank_transaction_risk`
- `employment_verification_score`
- `region`
- `employment_type`

The preprocessing pipeline performs numeric median imputation with missingness
indicators and categorical most-frequent imputation plus one-hot encoding.

## Evaluation-only demographic fields

These governance/evaluation attributes are excluded from the model input list:

- `sex`
- `age_group`
- `synthetic_demographic_group`

Raw `age` remains a model input; `age_group` is a distinct evaluation-only
field.

## Decision semantics

The model produces estimated default risk. The project decision threshold is
`0.50` for the deterministic synthetic evaluation/serving flow. This threshold
is a project assumption, not a real lending policy.

## Baseline evidence

Verified case-study evidence reports healthy ROC-AUC `0.8025`, Vendor B incident
ROC-AUC `0.7329`, healthy `device_risk_score` null rate `3.14%`, and Vendor B
null rate `22.00%`.

Generated repository evidence is authoritative if values change after a future
code/configuration update.

## Fairness and explainability

Fairness monitoring uses synthetic subgroup definitions for governance testing.
It does not establish legal fairness or non-discrimination. SHAP is used to
investigate model sensitivity and influential features; SHAP values are not
causal evidence.

## Governance

A candidate must pass data-quality, performance, calibration, drift, fairness,
and evidence-integrity gates before entering `STAGING`. Passing governance does
not permit direct production promotion; Phase 6 requires shadow and progressive
canary checks.

## Known limitations

Synthetic data/scenarios, no real applicant PII, no external population
validation, no real bank decision workflow, no causal fairness analysis, no
legal/regulatory certification, project-specific thresholds, a project-owned
registry/audit implementation, deterministic release simulation rather than
large-scale live traffic mirroring, and no claim of an active production AWS
environment.

See `docs/LIMITATIONS.md` for project-level limitations.
