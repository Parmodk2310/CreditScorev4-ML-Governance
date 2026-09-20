# Phase 10 — Root-Cause Ablation & Remediation Governance

Phase 10 extends the deterministic Vendor B incident with a controlled
root-cause experiment and evidence-backed remediation review. It does not alter
the production preprocessing path.

## Controlled 2x2 experiment

The Vendor B incident contains two synthetic interventions:

1. semantic score migration: attenuation, bias, and noise; and
2. elevated non-random `device_risk_score` missingness.

The experiment holds the applicant population, `default_30d` labels, trained
model artifact, and 0.50 decision threshold fixed.

| Scenario | Semantic shift | Elevated missingness | ROC-AUC | Approval | Approved default |
|---|---:|---:|---:|---:|---:|
| healthy | no | no | 0.8025 | 73.91% | 21.80% |
| semantic_only | yes | no | 0.7452 | 75.94% | 25.12% |
| missingness_only | no | yes | 0.7796 | 78.46% | 24.41% |
| combined | yes | yes | 0.7329 | 78.60% | 26.37% |

The missingness-only scenario reuses the exact Vendor B missingness mask while
preserving healthy observed score semantics. The combined scenario must
reproduce the stored Vendor B artifact.

## Root-cause interpretation

Within this deterministic synthetic fixture, semantic migration is the larger
contributor to ROC-AUC degradation while elevated missingness is the larger
contributor to approval inflation. Both factors increase the approved-cohort
30-day default rate. Their combined effect is not assumed to be additive
because the model is non-linear.

## Median-imputation diagnostic

For the 2,829 rows made newly missing by Vendor B:

- fitted training median: **0.4036**
- semantic reference mean: **0.4721**
- reference-minus-median gap: **+0.0685**

The counterfactual scorer preserves the fitted missingness indicator and changes
only the transformed numeric `device_risk_score` value. The median control
reproduces ordinary pipeline probabilities with zero measured delta.

This supports a scoped conclusion: for this synthetic missingness pattern, the
median numeric replacement path materially amplifies decision distortion. It
does not support the claim that median imputation is the sole root cause.

## Fixed-model remediation counterfactuals

| Candidate | ROC-AUC | Approval | Approved default | Status |
|---|---:|---:|---:|---|
| Current combined Vendor B | 0.7329 | 78.60% | 26.37% | blocked incident |
| Oracle semantic restore | 0.7451 | 75.96% | 25.13% | diagnostic only |
| q60 | 0.7402 | 76.12% | 25.28% | measured only |
| q75 | 0.7418 | 74.25% | 24.78% | validation candidate only |
| q90 | 0.7375 | 68.01% | 23.46% | measured; large approval contraction |

q75 is carried forward as a validation candidate because it reduces approval
distortion without the much larger approval contraction observed for q90. It
still leaves material ROC-AUC and approved-default gaps versus healthy
behavior, so it is not treated as a complete repair.

## Governance outcome

Vendor B remains **BLOCKED** by the existing Phase 2 data-quality control.
Phase 10 does not weaken that fail-closed boundary and does not change
production preprocessing.

## Verification

```bash
make quality
make phase10-verify
git diff --check
```

The cumulative gate preserves the Phase 1–9 chain, regenerates Phase 10
evidence, evaluates frozen outcome thresholds, and runs root-cause plus workflow
contract tests.

## Scope and non-claims

All evidence is deterministic and synthetic. Phase 10 does not establish a real
lending incident, real customer harm, regulatory compliance, a deployable oracle
fallback, or a universally safe q75 imputation policy.
