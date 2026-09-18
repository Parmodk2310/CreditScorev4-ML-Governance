# CreditScoreV4 ML Governance

> Production ML Incident Simulation, Remediation & Governance

## Current status

**Phase 1 — Incident Reproduction (`v0.1.0` target)**

This phase builds a deterministic synthetic lending scenario, trains a healthy CreditScoreV4 baseline on Vendor A data, then applies a schema-compatible Vendor B migration to the holdout population and evaluates the **same saved model**. The goal is to establish measurable incident evidence before adding monitoring or governance controls.

### Phase 1 scope

- [x] Synthetic lending data generator
- [x] Leakage-safe preprocessing and feature engineering
- [x] XGBoost CreditScoreV4 baseline
- [x] Vendor migration incident injector
- [x] Before/after model evaluation
- [x] Reproducible evidence artifacts
- [x] Unit and integration tests
- [ ] Phase 2 — Data quality governance
- [ ] Phase 3 — Drift governance
- [ ] Phase 4 — Fairness & explainability
- [ ] Phase 5 — Model governance
- [ ] Phase 6 — Safe serving & observability
- [ ] Phase 7 — Automation & cloud deployment

## Phase 1 data flow

```text
Synthetic lending population
          |
          v
   Vendor A (healthy)
          |
          +--> train CreditScoreV4
          |
          +--> healthy holdout --> baseline metrics

healthy holdout
      |
      v
Vendor B migration
(same schema, 22% device score missingness + semantic shift)
      |
      v
same saved CreditScoreV4
      |
      v
incident metrics
```

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Verify Phase 1

```bash
make phase1-verify
```

Generated evidence is written under `data/evidence/phase1/`. The README intentionally does not hard-code successful incident metrics; use the measured artifacts from your run.

## Important modeling semantics

`default_30d = 1` means the applicant defaulted within 30 days. The model predicts default risk probability. Protected/evaluation attributes are retained for later fairness analysis but are excluded from Phase 1 model features.
