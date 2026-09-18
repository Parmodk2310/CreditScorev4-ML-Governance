# Phase 1 Project Structure

```text
configs/phase1.yaml                  Experiment and acceptance configuration
src/creditscore/data/               Synthetic data, loading, preprocessing
src/creditscore/features/           Shared feature engineering
src/creditscore/incidents/          Vendor migration simulation
src/creditscore/model/              Train/evaluate/metrics/model persistence
src/creditscore/utils/              Configuration helpers
scripts/                             Reproducible Phase 1 CLI entry points
tests/unit/                          Component-level tests
tests/integration/                   Same-model incident degradation test
data/evidence/phase1/                Generated verification evidence
models/baseline/                     Generated serialized baseline model
```

Later-phase directories are intentionally omitted until their implementation begins.
