PYTHON ?= python
export PYTHONPATH := src$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: setup lint format typecheck phase1-generate phase1-train phase1-incident phase1-test phase1-verify phase1-clean phase2-healthy phase2-incident phase2-test phase2-verify phase2-clean quality

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	ruff check src/creditscore scripts tests

format:
	black src/creditscore scripts tests

# Package-mode checking avoids the src-layout duplicate-module ambiguity.
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
	$(PYTHON) -m pytest tests/unit tests/quality tests/integration

phase2-clean:
	rm -f data/evidence/phase2/*.json
	rm -f data/quarantine/phase2/*.csv

clean: phase1-clean phase2-clean
