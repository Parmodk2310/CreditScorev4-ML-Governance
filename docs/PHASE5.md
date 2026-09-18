# Phase 5 — Governance Policy Engine & Model Registry

## Objective

Phase 5 converts the evidence created by earlier controls into one deterministic, auditable model-promotion decision. It is intentionally a governance layer rather than a deployment layer.

## Evidence inputs

The workflow reuses the exact Phase 2–4 control implementations:

- data-quality contract + Great Expectations decision
- ROC-AUC / PR-AUC performance evidence
- Brier-score calibration evidence
- feature/prediction drift status
- subgroup fairness status
- content hashes for every referenced evidence artifact and the model artifact

## Policy gates

`configs/phase5.yaml` is the only place promotion thresholds and blocking statuses are defined. Defaults are project guardrails for this synthetic exercise, not universal or regulatory thresholds.

The policy currently blocks when:

- data quality is not `PASS`
- ROC-AUC or PR-AUC falls below configured minimums
- Brier score exceeds the configured maximum
- drift is `CRITICAL`
- fairness is `FAIL`
- evidence artifacts are incomplete or unhashed

## Registry state machine

```text
REGISTERED
    |
    v
CANDIDATE
   / \
  /   \
 v     v
STAGING REJECTED
```

`SHADOW`, `CANARY`, and `PRODUCTION` are reserved for Phase 6. A direct `CANDIDATE -> PRODUCTION` transition is intentionally illegal.

## Acceptance scenarios

### Healthy candidate

Vendor A is evaluated against itself. Quality, performance, calibration, drift, and fairness gates pass. The policy returns `APPROVE` and the registry moves `CANDIDATE -> STAGING`.

### Vendor C candidate

Vendor C remains contract-valid but has `CRITICAL` drift. The same policy returns `REJECT`; the drift gate is recorded as blocking and the version moves to `REJECTED`.

### Vendor D candidate

Vendor D remains contract-valid and aggregate-stable but fails configured subgroup fairness governance. The same policy returns `REJECT`; the fairness gate is recorded as blocking and the version moves to `REJECTED`.

## Auditability

Each candidate produces:

- normalized evidence JSON/CSV files
- SHA-256 content hashes
- deterministic decision ID
- gate-by-gate decision evidence
- blocking reasons
- registry state
- append-only JSONL audit events

Generated runtime artifacts are intentionally excluded from source control.

## Verification

```bash
make phase5-verify
```

The release gate verifies the healthy approval, both rejection scenarios, evidence hashes, audit record creation, registry persistence, illegal-transition protection, cumulative code quality, and the complete test suite.

## Scope boundary

Phase 5 does not deploy or serve a model. Phase 6 will consume an approved `STAGING` version and add API serving, shadow traffic, canary rollout, production promotion, runtime metrics, and rollback controls.
