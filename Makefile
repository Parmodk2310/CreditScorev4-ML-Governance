PYTHON ?= python
export PYTHONPATH := src$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: setup phase1-generate phase1-train phase1-incident phase1-test phase1-verify phase1-clean

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

phase1-generate:
	$(PYTHON) scripts/generate_dataset.py

phase1-train:
	$(PYTHON) scripts/train_baseline.py

phase1-incident:
	$(PYTHON) scripts/simulate_incident.py

phase1-test:
	$(PYTHON) -m pytest tests/unit tests/integration

phase1-verify:
	$(PYTHON) scripts/verify_phase1.py
	$(PYTHON) -m pytest tests/unit tests/integration

phase1-clean:
	rm -f data/raw/vendor_a/*.csv data/raw/vendor_b/*.csv
	rm -f data/evidence/phase1/*.json data/evidence/phase1/*.csv data/evidence/phase1/*.png
	rm -f models/baseline/*.joblib
