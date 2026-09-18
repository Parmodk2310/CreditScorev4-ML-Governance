# Phase 4 — Fairness & Explainability Governance

## Objective

Phase 4 demonstrates a governance gap that aggregate data-quality and drift controls cannot answer: a batch can be schema-valid and aggregate-stable while a model's decisions differ materially across an evaluation group.

This phase is a **synthetic governance stress test**, not a legal or regulatory determination.

## Vendor D scenario

Vendor D starts from the healthy Vendor A holdout. Only `group_c` in the evaluation-only `synthetic_demographic_group` field receives contract-valid shifts to three non-protected risk proxies:

- `device_risk_score`
- `credit_utilization`
- `bank_transaction_risk`

Protected/evaluation columns and the target are preserved exactly. None of the protected/evaluation columns enter model training or inference features.

## Control chain

```text
Vendor D
   |
   +--> Phase 2 contract/GX gate --> PASS
   |
   +--> Phase 3 aggregate PSI/KS --> STABLE
   |
   +--> Phase 4 subgroup assessment
              |
              +--> approval-rate disparity
              +--> demographic-parity evidence
              +--> equalized-odds evidence
              +--> SHAP proxy explanations
              |
              +--> fairness governance --> FAIL / REVIEW
```

## Decision semantics

The model predicts `P(default_30d=1)`. A default prediction uses `risk_probability >= 0.50`. The favorable lending outcome used for selection-rate analysis is `approved = risk_probability < 0.50`.

## Fairness evidence

Fairlearn `MetricFrame` produces group-disaggregated approval and classification metrics. Demographic-parity ratio/difference use the favorable approval decision. Equalized-odds difference uses default as the positive class.

Configured thresholds are project governance thresholds for the synthetic exercise. They are not proof of discrimination or regulatory compliance.

## Explainability evidence

SHAP `TreeExplainer` explains the fitted XGBoost classifier after the exact trained feature-engineering and preprocessing transforms. Evidence includes:

- global mean absolute SHAP importance
- group-level SHAP importance
- stressed-group signed SHAP delta
- local high-risk examples

The release gate explicitly verifies that `sex`, `age_group`, and `synthetic_demographic_group` are absent from both model-input features and SHAP feature space.

## Verification

```bash
make phase4-verify
```

The gate requires Vendor D to pass Phase 2, remain aggregate-STABLE under Phase 3, fail the configured primary fairness thresholds, generate SHAP evidence, and attribute the stressed group's risk increase to the intentionally shifted non-protected proxy features.
