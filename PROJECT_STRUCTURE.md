# Project Structure — Through Phase 6

```text
creditscorev4-ml-governance/
├── configs/
│   ├── phase1.yaml
│   ├── phase2.yaml
│   ├── phase3.yaml
│   ├── phase4.yaml
│   ├── phase5.yaml
│   └── phase6.yaml
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
│   ├── evidence/phase5/
│   ├── evidence/phase6/
│   ├── quarantine/phase2/
│   ├── quarantine/phase5/
│   ├── registry/
│   ├── audit/
│   └── release/
├── models/baseline/
├── src/creditscore/
│   ├── data/
│   ├── features/
│   ├── incidents/
│   ├── model/
│   ├── validation/
│   ├── drift/
│   ├── fairness/
│   ├── explainability/
│   ├── governance/
│   ├── serving/
│   │   ├── app.py
│   │   ├── schemas.py
│   │   ├── predictor.py
│   │   ├── health.py
│   │   └── metrics.py
│   └── release/
│       ├── models.py
│       ├── router.py
│       ├── gates.py
│       ├── rollback.py
│       └── controller.py
├── scripts/
│   ├── serve_model.py
│   ├── run_shadow.py
│   ├── run_canary.py
│   ├── simulate_rollback.py
│   ├── verify_phase1.py
│   ├── verify_phase2.py
│   ├── verify_phase3.py
│   ├── verify_phase4.py
│   ├── verify_phase5.py
│   └── verify_phase6.py
├── tests/
│   ├── unit/
│   ├── quality/
│   ├── drift/
│   ├── fairness/
│   ├── explainability/
│   ├── governance/
│   ├── serving/
│   ├── release/
│   └── integration/
├── docker/phase6/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── prometheus/prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       └── dashboards/phase6-serving.json
└── docs/
    ├── PHASE1.md
    ├── PHASE2.md
    ├── PHASE3.md
    ├── PHASE4.md
    ├── PHASE5.md
    └── PHASE6.md
```

Phase 7 owns workflow automation, CI/CD deployment, and cloud infrastructure.
