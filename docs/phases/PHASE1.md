# Phase 1 — Incident Reproduction

## Objective

Reproduce a controlled upstream-vendor failure in which an already-trained credit-risk model receives data from a migrated upstream vendor and materially loses discriminatory performance even though the external schema is still valid.

## Invariant

The model is trained once on healthy Vendor A history. It is **not retrained** for the incident experiment. The same serialized pipeline is evaluated on healthy and migrated holdout data.

## Vendor migration

Vendor B preserves column names, data types, and the nominal `[0, 1]` range of `device_risk_score`, but:

1. missingness rises from approximately 3% to approximately 22%;
2. the score distribution is compressed and noisier;
3. missingness is non-random and weighted toward higher pre-migration device risk.

The migration never uses the outcome label to decide which rows become missing.

## Phase 1 outputs

- `baseline_metrics.json`
- `incident_metrics.json`
- `performance_comparison.json`
- `missingness_comparison.csv`
- baseline and incident ROC plots
- serialized baseline model

## Definition of done

`make phase1-verify` passes the configured acceptance gates and all unit/integration tests pass.
