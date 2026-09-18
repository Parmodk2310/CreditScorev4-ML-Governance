# Project Structure — Through Phase 4

```text
creditscorev4-ml-governance/
├── configs/
│   ├── phase1.yaml
│   ├── phase2.yaml
│   ├── phase3.yaml
│   └── phase4.yaml
├── contracts/
│   └── credit_application_contract.yaml
├── data/
│   ├── raw/vendor_a/
│   ├── raw/vendor_b/
│   ├── raw/vendor_c/
│   ├── raw/vendor_d/
│   ├── reference/phase3/
│   ├── evidence/phase1/
│   ├── evidence/phase2/
│   ├── evidence/phase3/
│   ├── evidence/phase4/
│   └── quarantine/phase2/
├── models/baseline/
├── src/creditscore/
│   ├── data/
│   ├── features/
│   ├── incidents/
│   │   ├── vendor_migration.py
│   │   ├── vendor_c_drift.py
│   │   └── vendor_d_group_stress.py
│   ├── model/
│   ├── validation/
│   ├── drift/
│   ├── fairness/
│   │   ├── evaluator.py
│   │   ├── metrics.py
│   │   ├── models.py
│   │   └── report.py
│   └── explainability/
│       └── shap_engine.py
├── scripts/
│   ├── verify_phase1.py
│   ├── verify_phase2.py
│   ├── verify_phase3.py
│   ├── simulate_fairness_stress.py
│   ├── assess_fairness.py
│   ├── explain_model.py
│   └── verify_phase4.py
├── tests/
│   ├── unit/
│   ├── quality/
│   ├── drift/
│   ├── fairness/
│   ├── explainability/
│   └── integration/
└── docs/
    ├── PHASE1.md
    ├── PHASE2.md
    ├── PHASE3.md
    └── PHASE4.md
```

Later-phase registry, serving, rollout, observability, orchestration, and cloud infrastructure remain intentionally absent until their corresponding behavior is implemented and verified.
