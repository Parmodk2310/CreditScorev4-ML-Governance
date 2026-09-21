# Governance Policy

## Purpose

CreditScoreV4 treats model promotion as an evidence decision rather than a
deployment shortcut. Phase 5 evaluates a candidate against versioned blocking
gates, verifies evidence integrity, records a deterministic decision, and applies
only legal registry transitions.

The executable source of truth is `configs/phase5.yaml`. This document explains
that configuration; it does not replace it.

## Promotion gates

| Gate | Project rule | Blocking |
|---|---|---|
| Data quality | decision must be `PASS` | yes |
| Performance | ROC-AUC >= `0.75` | yes |
| Performance | PR-AUC >= `0.60` | yes |
| Calibration | Brier score <= `0.20` | yes |
| Drift | `CRITICAL` is blocked | yes |
| Fairness | `FAIL` is blocked | yes |
| Evidence integrity | at least 6 artifacts | yes |

All values above are engineering guardrails chosen for this synthetic case
study. They are not legal, regulatory, or industry-mandated thresholds.

## Evidence integrity

The governance workflow records SHA-256 hashes for evidence artifacts. The
decision identity is generated deterministically from the model identity,
scenario, policy, gate results, requested stage, and evidence hashes.

This supports two useful properties: the same evidence and policy produce the
same decision identity, and modified evidence can be detected before promotion.

## Expected decisions

| Scenario | Expected decision | Result |
|---|---|---|
| Healthy | `APPROVE` | `CANDIDATE -> STAGING` |
| Vendor C | `REJECT` | drift blocks promotion |
| Vendor D | `REJECT` | fairness blocks promotion |

## Registry state machine

Allowed transitions are implemented in `src/creditscore/governance/registry.py`:

```text
REGISTERED -> CANDIDATE
CANDIDATE -> STAGING
CANDIDATE -> REJECTED
STAGING -> SHADOW
SHADOW -> CANARY
SHADOW -> STAGING
CANARY -> PRODUCTION
CANARY -> STAGING
PRODUCTION -> terminal
REJECTED -> terminal
```

A direct `CANDIDATE -> PRODUCTION` transition is intentionally illegal.

## Governance vs release safety

Phase 5 answers whether a candidate is eligible to enter staging. Phase 6 asks
whether an approved staged candidate is healthy enough to progress toward
production. Passing model governance does not grant immediate production
status.

## Release guardrails

Configured in `configs/phase6.yaml`.

### Shadow

- maximum error rate: `0.02`
- maximum p95 latency: `250 ms`
- maximum mean risk delta: `0.05`
- minimum request count: `50`

### Canary

- maximum error rate: `0.03`
- maximum p95 latency: `300 ms`
- maximum mean risk delta: `0.06`
- minimum request count: `100`

Canary checkpoints are `10% -> 25% -> 50% -> 100%`.

A failed shadow/canary gate returns the candidate to `STAGING`.

## Deployment safety

Phase 7 defaults cloud mutation to disabled:

```text
AWS_DEPLOY_ENABLED=false
```

Deployment requires explicit opt-in and configured AWS/OIDC/Terraform
prerequisites.

## Policy-change procedure

A real change to governance thresholds should be treated as a governed software
change: state the reason, update versioned configuration, update tests,
regenerate evidence, review changed outcomes, update documentation, and merge
only after CI passes. Thresholds should never be changed merely to force a
candidate to pass.
