# Technical Deep Dive and Design Decisions

## System thesis

The project intentionally creates multiple failure modes that bypass different
layers of an ML system, then uses independent controls so each failure is
detected at the appropriate boundary before unsafe promotion.

```text
Vendor B -> data quality
Vendor C -> drift
Vendor D -> fairness
Healthy candidate -> governed release
Runtime degradation -> rollback
```

## Why evaluate the same model after Vendor B?

Retraining would mix two changes: upstream vendor behavior and model parameters.
Holding the trained model constant isolates the effect of the changed input
semantics/distribution.

## Why data quality and drift are separate

A data contract asks whether data conforms to expected structural/business
rules. Drift asks whether statistically valid data has changed relative to a
reference population. Vendor C is designed to pass the former and fail the
latter.

## Why PSI and KS together

PSI provides an interpretable binned distribution-shift signal. KS compares
empirical distributions without using the same binning. They are complementary
signals, not a claim that either metric is universally sufficient.

## Why fairness is separate from aggregate drift

Aggregate metrics can hide concentrated subgroup impact. Vendor D deliberately
creates that failure mode: aggregate drift remains stable while subgroup outcome
metrics cross project fairness thresholds.

## Why separate evaluation attributes from model inputs

`sex`, `age_group`, and `synthetic_demographic_group` are governance/evaluation
fields and are excluded from `MODEL_INPUT_FEATURES`.

Raw `age` remains a model input; `age_group` is a separate derived evaluation
attribute.

## Why SHAP is not causal proof

SHAP describes model attribution under the fitted model and observed/background
distribution. It can identify influential proxy features during investigation,
but it does not prove real-world causality.

## Why deterministic governance decisions

Governance needs reproducibility. The evaluator combines policy version, model
identity, scenario, gate results, requested stage, and evidence hashes into a
deterministic decision identity.

## Why hash evidence

A policy decision is only meaningful if referenced evidence has not been
silently modified. SHA-256 hashes provide integrity checks. They are not a
complete immutable-storage system; a production implementation would also need
durable access-controlled storage and retention rules.

## Why a project-owned registry instead of MLflow

The purpose was to make governance semantics explicit and inspectable: allowed
transitions, blocking behavior, evidence linkage, decision IDs, and audit
records.

A managed registry such as MLflow could later become a backend without changing
those policy semantics. Adding it only for a keyword would not improve the
current proof.

## Why not automatically retrain on drift

Drift can result from corruption, vendor semantic changes, population change,
instrumentation changes, or genuine concept change. Automatic retraining could
encode an upstream failure into a new model.

The project therefore treats drift as investigation/governance evidence rather
than an automatic retraining trigger.

## Why STAGING -> SHADOW -> CANARY -> PRODUCTION

Model eligibility and release safety are different concerns. A candidate may be
governance-eligible but still fail runtime compatibility, latency, error-rate,
or output-delta expectations. Progressive release limits exposure and creates
explicit rollback points.

## Why deterministic canary routing

Stable request bucketing makes routing reproducible in tests and demonstrations
and avoids per-request randomness obscuring rollout behavior. A real production
router may use infrastructure-level traffic management.

## Why ECS/Fargate rather than EKS

The demonstrated serving workload is stateless and does not require
Kubernetes-specific scheduling primitives. ECS/Fargate is sufficient to show
immutable containers, registry-backed images, service deployment, ALB health
checks, IAM/OIDC deployment controls, and Terraform-managed infrastructure with
less operational complexity.

## Why AWS deployment is disabled by default

Infrastructure code should not mutate a cloud account merely because a
developer runs local verification. `AWS_DEPLOY_ENABLED=false` makes no-mutation
the safe default and requires explicit deployment configuration.

## What changes for real production

A real deployment would need durable shared registry/audit/evidence storage,
concurrency-safe state transitions, access-control/approval ownership,
long-running monitoring history, alerts/on-call integration, SLOs/error budgets,
load/capacity testing, disaster recovery, retention policies, release
provenance/signing, environment apply/destroy evidence, and independent
validation/compliance review.

The project intentionally does not claim these are already implemented.
