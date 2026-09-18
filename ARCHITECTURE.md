# CreditScoreV4 ML Governance Architecture — Through Phase 2

```text
                         PHASE 1
Synthetic population
        |
        +------------------+
        |                  |
        v                  v
   Vendor A train     Vendor A holdout
        |                  |
        v                  v
 CreditScoreV4       healthy evaluation
        |                  |
        |             ROC-AUC ≈ 0.80
        |
        |           Phase 1 vendor migration
        |                  |
        |                  v
        |            Vendor B holdout
        |             same schema
        |             NULL ≈ 22%
        |                  |
        +----------------->v
                 same CreditScoreV4
                        |
                  ROC-AUC ≈ 0.73
                        |
                 incident evidence
                        |
                        v
                         PHASE 2
              versioned scoring contract
                        |
              +---------+----------+
              |                    |
              v                    v
        Domain validator    Great Expectations
              |                    |
              +---------+----------+
                        |
                 Data Quality Gate
                   /          \
                PASS          BLOCK
                 |              |
            downstream     quarantine
                            + JSON evidence
```

The design intentionally keeps Phase 2 upstream of model scoring/retraining. The gate blocks a batch because it violates declared data-quality controls. Statistical drift monitoring is a separate Phase 3 responsibility.
