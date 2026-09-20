# Phase 10 — Root-Cause Ablation & Remediation Evidence

Phase 10 extends the deterministic Vendor B incident with a controlled
root-cause experiment. Its purpose is to measure which parts of the synthetic
vendor migration contribute to the Phase 9 decision impact before making a
mechanism-specific claim.

## Controlled 2x2 experiment

The Vendor B incident contains two synthetic interventions:

1. a semantic score migration: attenuation, bias, and noise; and
2. elevated non-random `device_risk_score` missingness.

Phase 10 holds the applicant population, `default_30d` labels, trained model,
and 0.50 decision threshold fixed while evaluating:

| Scenario | Semantic shift | Elevated missingness |
|---|---:|---:|
| healthy | no | no |
| semantic_only | yes | no |
| missingness_only | no | yes |
| combined | yes | yes |

The missingness-only scenario uses the exact missingness mask from the combined
Vendor B fixture while preserving healthy observed score values. The combined
scenario must reproduce the existing Vendor B artifact.

For each scenario the analyzer records ROC-AUC, PR-AUC, Brier score, approval
rate, approved 30-day default rate, mean predicted risk, and decision
transitions relative to the healthy scenario. It also reports average main
effects and the semantic-by-missingness interaction.

Because the model is non-linear, these effects are descriptive for this
deterministic fixture and are not assumed to add linearly.

## Median-imputation diagnostic

The fitted baseline numeric pipeline uses median imputation with a missingness
indicator. Phase 10 records the fitted training median and the counterfactual
semantic Vendor B values for rows that become newly missing.

The counterfactual scorer preserves the fitted missingness indicator and
changes only the transformed numeric `device_risk_score` value. A median
control must reproduce the ordinary pipeline probabilities within numerical
tolerance. That control prevents the ablation helper from silently changing
other model inputs.

## Counterfactual remediation candidates

Phase 10 evaluates two categories without retraining the classifier.

### Oracle semantic restoration

For rows made newly missing by Vendor B, the analyzer restores the semantic
Vendor B value that would have existed without the missingness intervention,
while keeping the model's missingness indicator active.

This is a diagnostic counterfactual only. It is not deployable because the
lost value is known only inside the synthetic experiment.

### Healthy-training quantile fallbacks

The analyzer also measures predeclared 60th, 75th, and 90th percentile values
from observed healthy training `device_risk_score` data. Each candidate is
applied to missing incident rows while the fitted missingness indicator remains
active.

No candidate is selected in the first pass. The evidence must be reviewed
before freezing outcome-specific gates or changing the production-policy
simulation.

## Two-pass Phase 10 workflow

The first pass verifies experiment integrity rather than choosing thresholds
that force a desired conclusion:

```text
Phase 9 verified incident
        |
        v
2x2 controlled ablation
        |
        +--> semantic-only contribution
        +--> missingness-only contribution
        +--> interaction
        |
        v
median-control validation
        |
        v
oracle + q60/q75/q90 counterfactuals
        |
        v
review deterministic evidence
        |
        v
freeze Phase 10 outcome gates
        |
        v
promote CI/deploy preflight to phase10-verify
```

This sequencing prevents the project from inventing a root-cause narrative or
tuning an acceptance threshold to a preferred result.

## Operational boundary

The existing Phase 2 data-quality gate already blocks Vendor B because its
missingness violates the project contract. Phase 10 does not weaken that
fail-closed control. It provides mechanism evidence and remediation design for
the synthetic case study.

These measurements do not establish a real lending incident, real customer
harm, regulatory compliance, or a general causal claim about median
imputation.
