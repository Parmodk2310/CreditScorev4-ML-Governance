# Monitoring Plan

## Objective

The monitoring design separates different failure classes instead of reducing
system health to one composite score.

```text
data quality
  -> distribution drift
  -> fairness
  -> serving health
  -> release health
  -> investigation / rollback
```

All thresholds below are project guardrails for the synthetic case study.

## 1. Data-quality monitoring

Primary control: Phase 2 contract plus Great Expectations/custom validation.

Vendor B exercises the blocking path:

- healthy `device_risk_score` missingness: approximately `3.14%`
- incident missingness: `22.00%`
- expected action: `BLOCK` and quarantine

Response: stop the affected batch, preserve evidence, quarantine the batch,
investigate the upstream vendor/interface, and do not automatically retrain on
degraded data.

## 2. Distribution-drift monitoring

Phase 3 uses feature and prediction PSI/KS checks.

Project PSI levels:

- `< 0.10`: stable
- `0.10 .. < 0.20`: warning
- `>= 0.20`: critical

Project KS magnitude levels:

- `< 0.05`: stable
- `0.05 .. < 0.10` with statistical significance: warning
- `>= 0.10` with statistical significance: critical

Vendor C exercises drift handling separately from data quality: it passes
the contract but creates critical drift.

Critical drift blocks promotion and triggers investigation rather than automatic
retraining.

## 3. Fairness monitoring

Phase 4 monitors synthetic subgroup outcomes.

Project thresholds:

- demographic parity ratio: warning below `0.90`, fail below `0.80`
- selection-rate difference: warning at/above `0.10`, fail at/above `0.15`
- equalized-odds difference: warning at/above `0.10`, fail at/above `0.20`

A fairness `FAIL` blocks promotion.

These metrics are synthetic governance signals, not a legal fairness
determination.

## 4. Serving monitoring

The FastAPI service exposes Prometheus-compatible metrics through `/metrics`.
Relevant dimensions include request counts, latency, prediction outcomes, risk
distribution, readiness, rollout state, canary share, and rollback count.

`/health` and `/ready` provide separate process/readiness signals.

## 5. Shadow monitoring

Project guardrails:

- error rate <= `0.02`
- p95 latency <= `250 ms`
- mean risk delta <= `0.05`
- minimum request count >= `50`

A failed blocking gate returns the candidate to `STAGING`.

## 6. Canary monitoring

Project guardrails:

- error rate <= `0.03`
- p95 latency <= `300 ms`
- mean risk delta <= `0.06`
- minimum request count >= `100`

Progression: `10% -> 25% -> 50% -> 100%`.

Failed canary health returns the candidate to `STAGING` with a recorded rollback
reason.

## 7. Delivery monitoring

Phase 7 validates CI quality, tests, secret scanning, IaC scanning, container
smoke tests, Terraform validation, and explicit AWS deployment enablement.

Default cloud behavior is deny/no-mutation.

## 8. Evidence retention

Each monitoring layer writes machine-readable evidence under `data/evidence/`.
The Phase 8 evidence manifest summarizes where evidence exists; it does not
replace source artifacts.

## 9. Future production hardening

A production system would additionally need durable shared metric history,
alert routing/on-call ownership, explicit SLOs/error budgets, long-running trend
windows, release-to-metric correlation, concurrency/load validation, durable
governance/audit storage, failure injection, access controls, and retention
policies.
