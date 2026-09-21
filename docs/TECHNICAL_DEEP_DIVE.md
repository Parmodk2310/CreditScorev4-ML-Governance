# Technical Deep Dive and Design Decisions

## System thesis

The system uses multiple failure modes that bypass different layers of the ML
stack, with independent controls assigned to the boundary responsible for each
failure.

```text
Vendor B -> data quality
Vendor C -> drift
Vendor D -> fairness
Healthy candidate -> governed release
Runtime degradation -> rollback
```


## Architecture maps

- Complete figure index: [`ARCHITECTURE_FIGURES.md`](ARCHITECTURE_FIGURES.md)
- Canonical system view: [`assets/diagrams/system-overview.svg`](assets/diagrams/system-overview.svg)
- Governance/release model: [`assets/diagrams/governance-release-model.svg`](assets/diagrams/governance-release-model.svg)
- Delivery controls: [`assets/diagrams/delivery-controls.svg`](assets/diagrams/delivery-controls.svg)

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

Aggregate metrics can hide concentrated subgroup impact. Vendor D creates that
failure mode: aggregate drift remains stable while subgroup outcome
metrics cross project fairness thresholds.

## Why add intersectional fairness after single-axis fairness

A single protected dimension can look acceptable while a supported
intersection of dimensions experiences materially different outcomes. Phase 12
therefore evaluates `sex`, `synthetic_demographic_group`, and their
intersection separately.

Vendor E is constructed so aggregate drift is STABLE and the
single axes avoid blocking FAIL, while `female|group_c` crosses the project
intersectional thresholds. The result shows why aggregate and single-axis checks are not interchangeable
with intersectional governance.

## Why equal opportunity is reported separately from equalized odds

For this project the favorable decision is approval, and the favorable ground
truth is `default_30d == 0`. Equal-opportunity difference therefore compares
approval rates among applicants with favorable outcomes. Equalized odds also
incorporates the false-approval side among applicants with
`default_30d == 1`.

Reporting both prevents one metric name from hiding which conditional error
behavior changed.

## Why proxy-risk screening combines association with SHAP influence

Association alone can identify a feature that differs across a protected
intersection but barely affects model decisions. SHAP influence alone can
identify an important feature with little relationship to the protected
intersection.

Phase 12 requires both signals for review priority: incident-induced statistical
association and material model influence. Numeric association uses eta-squared;
categorical association uses Cramér's V. This remains screening evidence rather
than causal proof or a legal classification.

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

## Why Phase 11 uses a scheduler-independent orchestrator

The core orchestration semantics—task dependencies, fail-closed skipping,
command result handling, required evidence, SHA-256 capture, and run
serialization—live in Python rather than in a particular scheduler.

GitHub Actions is the concrete scheduler for this phase because the repository
needs one lightweight scheduled control run, not a separate scheduler database,
executor, worker fleet, and backfill control plane. The same task contract could
later be driven by Airflow, Dagster, Argo Workflows, or another system without
moving model-promotion authority into that scheduler.

## Why monitoring fails closed

A zero exit code is not sufficient evidence. Phase 11 also requires configured
evidence files after successful tasks. Missing evidence changes the task to
`FAIL`, and failed prerequisites cause dependent tasks to be `SKIPPED`.

This prevents a later governance step from appearing healthy when an earlier
control failed or failed to produce auditable evidence.

## Why scheduled monitoring does not retrain automatically

The Phase 11 configuration explicitly sets `automatic_retraining=false` and
`automatic_promotion=false`. A scheduler can detect and preserve evidence, but
it does not get a shortcut around the Phase 5 governance policy or Phase 6
safe-release state machine.

## Why AWS deployment is disabled by default

Infrastructure code should not mutate a cloud account merely because a
developer runs local verification. `AWS_DEPLOY_ENABLED=false` makes no-mutation
the safe default and requires explicit deployment configuration.

## Why incident operations are evidence-only

Phase 13 models detection, alert creation, governance blocking,
triage, and root-cause timing as deterministic operational evidence rather than
claiming a real production incident-response system.

The incident event stream is linked to existing Phase 2, Phase 9, and Phase 10
evidence with SHA-256 hashes. Configured project SLAs can therefore be evaluated
reproducibly without granting the alerting path authority to retrain, promote,
or remediate a model.

This keeps detection and evidence generation separate from remediation
authority, and avoids presenting synthetic timing measurements as production
MTTR or on-call performance.

## What changes for real production

A real deployment would need durable shared registry/audit/evidence storage,
concurrency-safe state transitions, access-control/approval ownership,
long-running monitoring history, alerts/on-call integration, SLOs/error budgets,
load/capacity testing, disaster recovery, retention policies, release
provenance/signing, environment apply/destroy evidence, and independent
validation/compliance review.

The project does not claim these are already implemented.
