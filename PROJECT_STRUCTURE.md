# Project Structure — Through Phase 5

```text
creditscorev4-ml-governance/
├── configs/
│   ├── phase1.yaml
│   ├── phase2.yaml
│   ├── phase3.yaml
│   ├── phase4.yaml
│   └── phase5.yaml
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
│   ├── quarantine/phase2/
│   ├── quarantine/phase5/
│   ├── registry/
│   └── audit/
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
│   └── governance/
│       ├── __init__.py
│       ├── models.py
│       ├── policy.py
│       ├── gates.py
│       ├── evaluator.py
│       ├── evidence.py
│       ├── registry.py
│       ├── audit_log.py
│       ├── decision.py
│       └── workflow.py
├── scripts/
│   ├── register_model.py
│   ├── evaluate_governance.py
│   ├── promote_model.py
│   ├── show_registry.py
│   ├── verify_phase1.py
│   ├── verify_phase2.py
│   ├── verify_phase3.py
│   ├── verify_phase4.py
│   └── verify_phase5.py
├── tests/
│   ├── unit/
│   ├── quality/
│   ├── drift/
│   ├── fairness/
│   ├── explainability/
│   ├── governance/
│   └── integration/
└── docs/
    ├── PHASE1.md
    ├── PHASE2.md
    ├── PHASE3.md
    ├── PHASE4.md
    └── PHASE5.md
```

Phase 6 owns serving, shadow/canary rollout, observability, and rollback. Phase 7 owns workflow automation and cloud deployment.
