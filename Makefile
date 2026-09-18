PYTHON ?= python
export PYTHONPATH := src$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: setup lint format typecheck quality phase1-generate phase1-train phase1-incident phase1-test phase1-verify phase1-clean phase2-healthy phase2-incident phase2-test phase2-verify phase2-clean phase3-simulate phase3-drift phase3-test phase3-verify phase3-clean phase4-simulate phase4-fairness phase4-explain phase4-test phase4-verify phase4-clean phase5-register phase5-evaluate phase5-demo phase5-test phase5-verify phase5-clean clean

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
	$(PYTHON) -m pytest tests/unit tests/quality tests/drift tests/fairness tests/explainability tests/governance tests/integration

phase5-clean:
	rm -rf data/evidence/phase5/*
	rm -f data/registry/phase5_registry.json
	rm -f data/audit/phase5_audit.jsonl
	rm -f data/quarantine/phase5/*.csv

clean: phase1-clean phase2-clean phase3-clean phase4-clean phase5-clean
