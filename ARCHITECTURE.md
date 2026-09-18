# CreditScoreV4 Architecture — Phase 1

```text
                           PHASE 1

Synthetic Lending Population
            |
            v
    +----------------+
    | Vendor A       |
    | healthy source |
    +-------+--------+
            |
       +----+---------------------+
       |                          |
       v                          v
Training split               Healthy holdout
       |                          |
       v                          |
CreditScoreV4                    |
XGBoost pipeline                 |
       |                          |
       +------ serialized --------+
                                  |
                                  +--> Baseline evaluation
                                  |
                                  v
                         Vendor migration
                         same schema/range
                         missingness + semantic shift
                                  |
                                  v
                           Vendor B holdout
                                  |
                                  v
                       SAME serialized model
                                  |
                                  v
                         Incident evaluation
                                  |
                                  v
                           Evidence artifacts
```

No monitoring or governance control is implemented in Phase 1. Those controls are introduced only after the failure is reproducibly demonstrated.
