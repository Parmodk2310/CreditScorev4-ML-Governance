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

## Phase 4 — subgroup fairness and explainability

```text
Vendor A reference ----------------------------+
                                              |
Vendor D subgroup proxy stress                |
       |                                      |
       +--> Phase 2 quality gate --> PASS     |
       |                                      |
       +--> Phase 3 aggregate drift --> STABLE|
       |                                      |
       +------------------+-------------------+
                          |
                          v
                  same CreditScoreV4
                          |
              +-----------+-----------+
              |                       |
              v                       v
      Fairlearn subgroup          SHAP TreeExplainer
           metrics                    |
              |                       |
              +-----------+-----------+
                          v
                Phase 4 evidence / FAIL
```

Protected/evaluation columns (`sex`, `age_group`, `synthetic_demographic_group`) remain outside `MODEL_INPUT_FEATURES`. Phase 4 uses them only after inference to evaluate subgroup behavior. Vendor D changes non-protected proxy features only for a synthetic evaluation group, while preserving schema, target, and protected values.
