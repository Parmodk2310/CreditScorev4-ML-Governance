# Project Structure — Through Phase 3

```text
creditscorev4-ml-governance/
├── configs/
│   ├── phase1.yaml
│   ├── phase2.yaml
│   └── phase3.yaml
├── contracts/
│   └── credit_application_contract.yaml
├── data/
│   ├── raw/vendor_a/
│   ├── raw/vendor_b/
│   ├── raw/vendor_c/
│   ├── reference/phase3/
│   ├── evidence/phase1/
│   ├── evidence/phase2/
│   ├── evidence/phase3/
│   └── quarantine/phase2/
├── models/baseline/
├── src/creditscore/
│   ├── data/
│   ├── features/
│   ├── incidents/
│   │   ├── vendor_migration.py
│   │   └── vendor_c_drift.py
│   ├── model/
│   ├── validation/
│   └── drift/
│       ├── detector.py
│       ├── ks.py
│       ├── models.py
│       ├── psi.py
│       └── report.py
├── scripts/
│   ├── verify_phase1.py
│   ├── verify_phase2.py
│   ├── simulate_drift.py
│   ├── check_drift.py
│   └── verify_phase3.py
├── tests/
│   ├── unit/
│   ├── quality/
│   ├── drift/
│   └── integration/
└── docs/
    ├── PHASE1.md
    ├── PHASE2.md
    └── PHASE3.md
```

Later-phase infrastructure is intentionally absent until its corresponding behavior is implemented and verified.
