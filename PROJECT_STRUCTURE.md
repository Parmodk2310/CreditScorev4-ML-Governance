# Project Structure — Through Phase 2

```text
creditscorev4-ml-governance/
├── configs/
│   ├── phase1.yaml
│   └── phase2.yaml
├── contracts/
│   └── credit_application_contract.yaml
├── data/
│   ├── raw/
│   │   ├── vendor_a/
│   │   └── vendor_b/
│   ├── evidence/
│   │   ├── phase1/
│   │   └── phase2/
│   └── quarantine/
│       └── phase2/
├── models/
│   └── baseline/
├── src/creditscore/
│   ├── data/
│   ├── features/
│   ├── incidents/
│   ├── model/
│   ├── utils/
│   └── validation/
│       ├── contract.py
│       ├── gate.py
│       ├── gx_engine.py
│       ├── models.py
│       └── validator.py
├── scripts/
│   ├── generate_dataset.py
│   ├── train_baseline.py
│   ├── simulate_incident.py
│   ├── verify_phase1.py
│   ├── validate_data_quality.py
│   └── verify_phase2.py
├── tests/
│   ├── unit/
│   ├── quality/
│   └── integration/
├── docs/
│   ├── PHASE1.md
│   └── PHASE2.md
├── Makefile
├── pyproject.toml
├── ARCHITECTURE.md
└── README.md
```

Only implemented phases are expanded. Airflow, MLflow, FastAPI, monitoring, Docker orchestration, Terraform, and Kubernetes are intentionally not added as empty placeholders.
