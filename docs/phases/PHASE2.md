# Phase 2 — Data Quality Governance

Phase 2 adds a blocking data-quality control in front of CreditScoreV4. It deliberately reuses the deterministic Vendor B incident generated in Phase 1; there is no new synthetic failure for this phase.

## Question answered

Could the upstream vendor migration have been stopped before the degraded batch reached model scoring or retraining?

## Control path

```text
Phase 1 Vendor A / Vendor B batches
               |
               v
        Versioned Data Contract
               |
       +-------+---------+
       |                 |
       v                 v
Domain validator    Great Expectations
       |                 |
       +-------+---------+
               |
         Data Quality Gate
          /           \
       PASS           BLOCK
        |               |
   downstream      quarantine + evidence
```

## Contracted controls

- required scoring columns
- logical types
- uniqueness of `application_id`
- numeric ranges
- controlled categories
- missingness thresholds
- `device_risk_score` may be missing in at most 5% of rows

Vendor A is expected to pass at roughly 3% device-score missingness. The exact Vendor B incident from Phase 1 is expected to fail at roughly 22% and be quarantined.

## Important boundary

Phase 2 does **not** detect distribution drift with PSI or KS. That is Phase 3. Phase 2 blocks the current incident because it violates a declared data-quality contract, not because a drift statistic is high.
