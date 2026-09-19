# Apply Phase 2

1. Finish and push the latest `phase/1-incident-baseline` branch.
2. Verify type checking in package mode with `mypy -p creditscore`. If an old scaffold left `src/__init__.py`, remove it because `src/` is a source root, not a Python package.
3. Create `phase/2-data-quality-governance` from the verified Phase 1 tip.
4. Overlay this cumulative package on that branch.
5. Install with `python -m pip install -e ".[dev]"`.
6. Run `make phase2-verify`.
7. Review generated evidence under `data/evidence/phase2/` and the blocked Vendor B copy under `data/quarantine/phase2/`.

The Phase 2 verification gate regenerates Phase 1 first, then validates the exact resulting Vendor A and Vendor B batches.
