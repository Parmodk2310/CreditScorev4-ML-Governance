PYTHON ?= python
export PYTHONPATH := src$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: setup lint format typecheck quality phase1-generate phase1-train phase1-incident phase1-test phase1-verify phase1-clean phase2-healthy phase2-incident phase2-test phase2-verify phase2-clean phase3-simulate phase3-drift phase3-test phase3-verify phase3-clean phase4-simulate phase4-fairness phase4-explain phase4-test phase4-verify phase4-clean phase5-register phase5-evaluate phase5-demo phase5-test phase5-verify phase5-clean phase6-serve phase6-shadow phase6-canary phase6-rollback phase6-demo phase6-test phase6-verify phase6-clean phase7-manifest phase7-gate phase7-test phase7-verify phase7-terraform phase7-clean clean

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	ruff check src/creditscore scripts tests

format:
	black src/creditscore scripts tests

typecheck:
	mypy -p creditscore

quality: lint typecheck
	black --check src/creditscore scripts tests
	$(PYTHON) -m compileall -q src/creditscore scripts tests

phase1-generate:
	$(PYTHON) scripts/generate_dataset.py

phase1-train:
	$(PYTHON) scripts/train_baseline.py

phase1-incident:
	$(PYTHON) scripts/simulate_incident.py

phase1-test:
	$(PYTHON) -m pytest tests/unit tests/integration/test_incident_pipeline.py

phase1-verify:
	$(PYTHON) scripts/verify_phase1.py
	$(PYTHON) -m pytest tests/unit tests/integration/test_incident_pipeline.py

phase1-clean:
	rm -f data/raw/vendor_a/*.csv data/raw/vendor_b/*.csv
	rm -f data/evidence/phase1/*.json data/evidence/phase1/*.csv data/evidence/phase1/*.png
	rm -f models/baseline/*.joblib

phase2-healthy:
	$(PYTHON) scripts/validate_data_quality.py --input data/raw/vendor_a/holdout.csv --source vendor_a --batch-name vendor_a_healthy

phase2-incident:
	$(PYTHON) scripts/validate_data_quality.py --input data/raw/vendor_b/holdout.csv --source vendor_b --batch-name vendor_b_incident || test $$? -eq 2

phase2-test:
	$(PYTHON) -m pytest tests/quality tests/integration/test_phase2_quality_gate.py

phase2-verify:
	$(PYTHON) scripts/verify_phase1.py
	$(PYTHON) scripts/verify_phase2.py
	$(PYTHON) -m pytest tests/unit tests/quality tests/integration/test_incident_pipeline.py tests/integration/test_phase2_quality_gate.py

phase2-clean:
	rm -f data/evidence/phase2/*.json
	rm -f data/quarantine/phase2/*.csv

phase3-simulate:
	$(PYTHON) scripts/simulate_drift.py

phase3-drift: phase3-simulate
	$(PYTHON) scripts/check_drift.py

phase3-test:
	$(PYTHON) -m pytest tests/drift tests/integration/test_phase3_drift_pipeline.py

phase3-verify:
	$(PYTHON) scripts/verify_phase1.py
	$(PYTHON) scripts/verify_phase2.py
	$(PYTHON) scripts/verify_phase3.py
	$(PYTHON) -m pytest tests/unit tests/quality tests/drift tests/integration/test_incident_pipeline.py tests/integration/test_phase2_quality_gate.py tests/integration/test_phase3_drift_pipeline.py

phase3-clean:
	rm -f data/raw/vendor_c/*.csv
	rm -f data/reference/phase3/*.json
	rm -f data/evidence/phase3/*.json data/evidence/phase3/*.csv
	rm -f data/evidence/phase2/vendor_c_drift_quality_report.json

phase4-simulate:
	$(PYTHON) scripts/simulate_fairness_stress.py

phase4-fairness: phase4-simulate
	$(PYTHON) scripts/assess_fairness.py

phase4-explain: phase4-simulate
	$(PYTHON) scripts/explain_model.py

phase4-test:
	$(PYTHON) -m pytest tests/fairness tests/explainability tests/integration/test_phase4_fairness_pipeline.py

phase4-verify:
	$(PYTHON) scripts/verify_phase1.py
	$(PYTHON) scripts/verify_phase2.py
	$(PYTHON) scripts/verify_phase3.py
	$(PYTHON) scripts/verify_phase4.py
	$(PYTHON) -m pytest tests/unit tests/quality tests/drift tests/fairness tests/explainability tests/integration/test_incident_pipeline.py tests/integration/test_phase2_quality_gate.py tests/integration/test_phase3_drift_pipeline.py tests/integration/test_phase4_fairness_pipeline.py

phase4-clean:
	rm -f data/raw/vendor_d/*.csv
	rm -f data/evidence/phase4/*.json data/evidence/phase4/*.csv
	rm -f data/evidence/phase2/vendor_d_fairness_quality_report.json


phase5-register:
	$(PYTHON) scripts/register_model.py --scenario healthy

phase5-evaluate:
	$(PYTHON) scripts/evaluate_governance.py --scenario healthy

phase5-demo:
	$(PYTHON) scripts/verify_phase5.py

phase5-test:
	$(PYTHON) -m pytest tests/governance tests/integration/test_phase5_governance_pipeline.py

phase5-verify:
	$(PYTHON) scripts/verify_phase1.py
	$(PYTHON) scripts/verify_phase2.py
	$(PYTHON) scripts/verify_phase3.py
	$(PYTHON) scripts/verify_phase4.py
	$(PYTHON) scripts/verify_phase5.py
	$(PYTHON) -m pytest tests/unit tests/quality tests/drift tests/fairness tests/explainability tests/governance tests/integration/test_incident_pipeline.py tests/integration/test_phase2_quality_gate.py tests/integration/test_phase3_drift_pipeline.py tests/integration/test_phase4_fairness_pipeline.py tests/integration/test_phase5_governance_pipeline.py

phase5-clean:
	rm -rf data/evidence/phase5/*
	rm -f data/registry/phase5_registry.json
	rm -f data/audit/phase5_audit.jsonl
	rm -f data/quarantine/phase5/*.csv

phase6-serve:
	$(PYTHON) scripts/serve_model.py

phase6-shadow:
	$(PYTHON) scripts/run_shadow.py

phase6-canary:
	$(PYTHON) scripts/run_canary.py

phase6-rollback:
	$(PYTHON) scripts/simulate_rollback.py

phase6-demo:
	$(PYTHON) scripts/verify_phase6.py

phase6-test:
	$(PYTHON) -m pytest tests/serving tests/release tests/integration/test_phase6_safe_release_pipeline.py

phase6-verify:
	$(PYTHON) scripts/verify_phase1.py
	$(PYTHON) scripts/verify_phase2.py
	$(PYTHON) scripts/verify_phase3.py
	$(PYTHON) scripts/verify_phase4.py
	$(PYTHON) scripts/verify_phase5.py
	$(PYTHON) scripts/verify_phase6.py
	$(PYTHON) -m pytest tests/unit tests/quality tests/drift tests/fairness tests/explainability tests/governance tests/serving tests/release tests/integration/test_incident_pipeline.py tests/integration/test_phase2_quality_gate.py tests/integration/test_phase3_drift_pipeline.py tests/integration/test_phase4_fairness_pipeline.py tests/integration/test_phase5_governance_pipeline.py tests/integration/test_phase6_safe_release_pipeline.py

phase6-clean:
	rm -f data/evidence/phase6/*.json
	rm -f data/release/*.json
	rm -f data/audit/phase6_*.jsonl

phase7-manifest:
	$(PYTHON) scripts/write_release_manifest.py --image-digest sha256:phase7-local-verification --output data/evidence/phase7/release_manifest.json

phase7-gate:
	$(PYTHON) scripts/check_deployment_gate.py

phase7-test:
	$(PYTHON) -m pytest tests/automation tests/deployment tests/integration/test_phase7_automation_pipeline.py

phase7-verify:
	$(PYTHON) scripts/verify_phase1.py
	$(PYTHON) scripts/verify_phase2.py
	$(PYTHON) scripts/verify_phase3.py
	$(PYTHON) scripts/verify_phase4.py
	$(PYTHON) scripts/verify_phase5.py
	$(PYTHON) scripts/verify_phase6.py
	$(PYTHON) scripts/verify_phase7.py
	$(PYTHON) -m pytest tests/unit tests/quality tests/drift tests/fairness tests/explainability tests/governance tests/serving tests/release tests/automation tests/deployment tests/integration/test_incident_pipeline.py tests/integration/test_phase2_quality_gate.py tests/integration/test_phase3_drift_pipeline.py tests/integration/test_phase4_fairness_pipeline.py tests/integration/test_phase5_governance_pipeline.py tests/integration/test_phase6_safe_release_pipeline.py tests/integration/test_phase7_automation_pipeline.py

phase7-terraform:
	terraform fmt -check -recursive infra/terraform
	terraform -chdir=infra/terraform init -backend=false -input=false
	terraform -chdir=infra/terraform validate

phase7-clean:
	rm -f data/evidence/phase7/*.json

clean: phase1-clean phase2-clean phase3-clean phase4-clean phase5-clean phase6-clean phase7-clean phase8-clean phase9-clean phase10-clean


# Phase 8 — governance evidence and reviewer experience
.PHONY: phase8-test phase8-verify phase8-clean

phase8-test:
	$(PYTHON) -m pytest tests/evidence

phase8-verify:
	$(MAKE) phase7-verify
	$(PYTHON) scripts/verify_phase8.py
	$(PYTHON) -m pytest tests/evidence

phase8-clean:
	rm -f data/evidence/phase8/*.json

# Phase 9 — business impact & incident outcome evidence
.PHONY: phase9-analyze phase9-test phase9-verify phase9-clean

phase9-analyze:
	$(PYTHON) scripts/analyze_business_impact.py

phase9-test:
	$(PYTHON) -m pytest tests/business_impact tests/integration/test_phase9_business_impact_pipeline.py

phase9-verify:
	$(MAKE) phase8-verify
	$(PYTHON) scripts/analyze_business_impact.py
	$(PYTHON) scripts/verify_phase9.py
	$(PYTHON) -m pytest tests/business_impact tests/integration/test_phase9_business_impact_pipeline.py

phase9-clean:
	rm -f data/evidence/phase9/*.json data/evidence/phase9/*.csv

# Phase 10 — root-cause ablation & remediation evidence
.PHONY: phase10-analyze phase10-test phase10-verify phase10-clean

phase10-analyze:
	$(PYTHON) scripts/analyze_root_cause.py

phase10-test:
	$(PYTHON) -m pytest tests/root_cause tests/integration/test_phase10_root_cause_pipeline.py

phase10-verify:
	$(MAKE) phase9-verify
	$(PYTHON) scripts/analyze_root_cause.py
	$(PYTHON) scripts/verify_phase10.py
	$(PYTHON) -m pytest tests/root_cause tests/integration/test_phase10_root_cause_pipeline.py

phase10-clean:
	rm -f data/evidence/phase10/*.json data/evidence/phase10/*.csv
