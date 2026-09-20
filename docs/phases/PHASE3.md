# Phase 3 — Statistical Drift Governance

Phase 3 proves that passing a deterministic data contract does not guarantee a batch is statistically safe.

## Scenario

Phase 1 produced healthy Vendor A and a degraded Vendor B incident. Phase 2 correctly blocks Vendor B because its `device_risk_score` missingness exceeds the 5% contract limit.

Phase 3 introduces **Vendor C**. Vendor C intentionally preserves the Phase 2 schema, types, ranges, categories, uniqueness, row count, and `device_risk_score` missingness. It therefore passes the Phase 2 gate. However, selected continuous features are shifted enough to change both feature distributions and CreditScoreV4's predicted-risk distribution.

## Detection

Phase 3 combines:

- Population Stability Index (PSI), using quantile bins derived only from the healthy Vendor A reference.
- Two-sample Kolmogorov-Smirnov statistics using SciPy.
- Configurable severity thresholds.
- Feature-level and output/prediction drift.
- Stable control features that are not modified by Vendor C.

Configured operational thresholds are project controls, not regulatory standards.

## Expected behavior

```text
Vendor C
  |
  +--> Phase 2 contract + GX ........ PASS
  |
  +--> PSI / KS
          |
          +--> unchanged controls ... STABLE
          +--> selected features .... WARNING / CRITICAL
          +--> risk probabilities ... WARNING / CRITICAL
          |
          +--> overall .............. CRITICAL
```

## Verification

```bash
make phase3-verify
```

The release gate regenerates Phase 1, re-verifies Phase 2, creates Vendor C, proves Vendor C passes Phase 2, computes feature and score drift, writes machine-readable evidence, and runs cumulative tests.
