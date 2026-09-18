# Phase 1 Package Manifest

This package is the complete Phase 1 source/config/test overlay for `creditscorev4-ml-governance`.

## Verification performed before packaging

- End-to-end Phase 1 acceptance run: PASS
- Unit + integration tests: 8 passed
- Python compile check: PASS
- Measured reference run (Python 3.12 environment):
  - baseline ROC-AUC: 0.8016
  - incident ROC-AUC: 0.7325
  - AUC degradation: 0.0691
  - baseline `device_risk_score` NULL rate: 3.14%
  - incident `device_risk_score` NULL rate: 22.00%

These are deterministic reference outputs for the tested dependency versions; your generated artifacts remain the source of truth for your own run.
