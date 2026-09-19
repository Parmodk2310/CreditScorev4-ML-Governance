# Project Structure — Through Phase 8

```text
creditscorev4-ml-governance/
├── configs/
│   ├── phase1.yaml
│   ├── phase2.yaml
│   ├── phase3.yaml
│   ├── phase4.yaml
│   ├── phase5.yaml
│   ├── phase6.yaml
│   └── phase7.yaml
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
│   ├── evidence/phase7/
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
│   ├── verify_phase6.py
│   ├── verify_phase7.py
│   ├── check_deployment_gate.py
│   ├── write_release_manifest.py
│   └── verify_container.py
├── tests/
│   ├── unit/
│   ├── quality/
│   ├── drift/
│   ├── fairness/
│   ├── explainability/
│   ├── governance/
│   ├── serving/
│   ├── release/
│   ├── automation/
│   ├── deployment/
│   └── integration/
├── docker/phase6/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── prometheus/prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       └── dashboards/phase6-serving.json
├── .github/workflows/
│   ├── ci.yml
│   ├── security.yml
│   ├── image.yml
│   └── deploy.yml
├── infra/terraform/
│   ├── versions.tf
│   ├── providers.tf
│   ├── variables.tf
│   ├── networking.tf
│   ├── ecr.tf
│   ├── iam.tf
│   ├── ecs.tf
│   └── outputs.tf
└── docs/
    ├── PHASE1.md
    ├── PHASE2.md
    ├── PHASE3.md
    ├── PHASE4.md
    ├── PHASE5.md
    ├── PHASE6.md
    └── PHASE7.md
```

Phase 7 implements workflow automation, security gates, immutable image verification, and a fail-closed Terraform ECS/Fargate deployment path.

<!-- PHASE8_STRUCTURE -->
## Phase 8 additions

```text
configs/
└── phase8.yaml

data/evidence/phase8/
└── .gitkeep
   # reviewer_evidence_manifest.json is generated

scripts/
└── verify_phase8.py

tests/evidence/
└── test_phase8_evidence_contract.py

docs/
├── PHASE8.md
├── GOVERNANCE_POLICY.md
├── MODEL_CARD.md
├── MODEL_VALIDATION_REPORT.md
├── MONITORING_PLAN.md
├── LIMITATIONS.md
├── EVIDENCE_INDEX.md
├── TECHNICAL_DEEP_DIVE.md
├── REPRODUCIBLE_DEMO.md
└── history/
    ├── PHASE1_APPLY.md
    └── PHASE2_APPLY.md
```
