# CreditScoreV4 ML Governance Architecture — Through Phase 3

```text
                         PHASE 1
Vendor A train ----------------------> CreditScoreV4
Vendor A holdout -------------------> healthy evaluation (~0.80 AUC)
        |
        +--> Vendor B migration ----> same model (~0.73 AUC)
                         |
                         v
                         PHASE 2
              versioned data contract
                 + Great Expectations
                         |
                  Vendor B --> BLOCK
                    quarantine/evidence
                         |
                         v
                         PHASE 3
Vendor A reference -------------------------------+
                                                   |
Vendor C: schema/type/range/null contract valid    |
        |                                          |
        +--> Phase 2 gate --> PASS                 |
        |                                          |
        +--> feature PSI + KS <--------------------+
        |
        +--> same CreditScoreV4
                 |
                 +--> prediction PSI + KS
                         |
                  STABLE/WARNING/CRITICAL
                         |
                    drift evidence
```

Phase 3 intentionally separates statistical drift from deterministic data quality. Passing Phase 2 is a precondition for the Vendor C drift demonstration.
