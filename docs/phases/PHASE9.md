# Phase 9 — Business Impact & Incident Outcome Evidence

## Objective

Phase 9 connects the already-verified Vendor B technical failure to a
measurable decision and observed-outcome impact.

The project continues to use deterministic synthetic data. The phase does not
claim a real bank incident, actual customer harm, or regulatory impact.

## Why this phase exists

Phase 1 proves that the same CreditScoreV4 model degrades under the Vendor B
migration:

- ROC-AUC: `0.8025 -> 0.7329`
- `device_risk_score` missingness: `3.14% -> 22.00%`

Phase 9 asks the next question:

> What happens to approval decisions and the observed 30-day default rate among
> approved applicants when the scoring input degrades?

## Controlled comparison

Vendor A and Vendor B use the same ordered holdout applicants and preserve the
same `default_30d` labels. Only the upstream vendor representation changes.

This lets the phase isolate decision impact without pretending that the
underlying applicant population itself changed.

```text
Same applicants + same outcome labels
               |
        +------+------+
        |             |
        v             v
   Vendor A       Vendor B
    healthy       migration
        |             |
        +------ same model ------+
                     |
                     v
               approval decisions
                     |
                     v
          approved-cohort outcomes
```

## Current deterministic evidence

The Phase 9 baseline was established from the current Phase 1 fixture:

| Metric | Healthy Vendor A | Vendor B incident | Change |
|---|---:|---:|---:|
| Approval rate | `73.91%` | `78.60%` | `+4.69 pp` |
| Approved 30-day default rate | `21.80%` | `26.37%` | `+4.57 pp` |
| Mean predicted risk | `0.3414` | `0.3274` | `-0.0140` |
| Device-risk missingness | `3.14%` | `22.00%` | `+18.86 pp` |
| Overall default rate | `33.87%` | `33.87%` | unchanged |

The unchanged overall outcome rate is an important control: the comparison uses
the same labels. The degraded vendor representation causes the model to
underestimate average risk while approving a larger and riskier cohort.

This is project evidence from a synthetic fixture, not an estimate of
real-world lending loss.

## Decision-transition evidence

Phase 9 also records:

- healthy reject -> incident approve applicants,
- healthy approve -> incident reject applicants,
- total decision flips,
- decision-flip rate,
- observed 30-day default rate of the newly approved cohort.

These metrics make the business-impact analysis more informative than a model
performance metric alone.

## Evidence artifacts

Phase 9 generates:

- `data/evidence/phase9/business_impact.json`
- `data/evidence/phase9/cohort_summary.csv`
- `data/evidence/phase9/decision_transition_summary.json`

The JSON report includes SHA-256 hashes for the healthy holdout, incident
holdout, and persisted model artifact.

## Acceptance contract

The phase requires:

- the same ordered applicant population,
- identical outcome labels,
- healthy approval rate within the known deterministic range,
- incident approval rate within the known deterministic range,
- at least a 4 percentage-point approval-rate increase,
- at least a 4 percentage-point increase in approved-cohort 30-day default,
- a measurable decrease in model-predicted average risk,
- at least an 18 percentage-point increase in device-risk missingness,
- effectively unchanged overall default rate,
- traceability hashes for the source datasets and model artifact.

The acceptance ranges are regression contracts for this synthetic incident,
not business or regulatory limits.

## Verification

```bash
make phase9-verify
```

A passing result means the technical Vendor B incident is linked to a
reproducible business-impact signal without inventing unsupported headline
metrics.

## Phase boundary

Phase 9 quantifies the decision/outcome impact. It does **not** yet prove which
preprocessing behavior caused that impact.

Root-cause ablation and the specific role of median imputation belong to the
next phase.
