"""Blocking data-quality gate with evidence and quarantine semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .contract import DataContract
from .gx_engine import validate_with_gx
from .validator import DataContractValidator


@dataclass(frozen=True)
class GateDecision:
    batch_name: str
    source: str
    decision: str
    contract_passed: bool
    gx_passed: bool
    failed_rule_ids: list[str]
    batch_fingerprint: str
    evidence_path: str
    quarantine_path: str | None

    @property
    def passed(self) -> bool:
        return self.decision == "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_name": self.batch_name,
            "source": self.source,
            "decision": self.decision,
            "contract_passed": self.contract_passed,
            "gx_passed": self.gx_passed,
            "failed_rule_ids": self.failed_rule_ids,
            "batch_fingerprint": self.batch_fingerprint,
            "evidence_path": self.evidence_path,
            "quarantine_path": self.quarantine_path,
        }


class DataQualityGate:
    """Run independent contract + GX checks and block unsafe batches."""

    def __init__(
        self,
        contract: DataContract,
        *,
        evidence_dir: str | Path,
        quarantine_dir: str | Path,
    ):
        self.contract = contract
        self.evidence_dir = Path(evidence_dir)
        self.quarantine_dir = Path(quarantine_dir)
        self.validator = DataContractValidator(contract)

    def evaluate(self, frame: pd.DataFrame, *, batch_name: str, source: str) -> GateDecision:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

        contract_report = self.validator.validate(frame, batch_name=batch_name, source=source)
        gx_report = validate_with_gx(frame, self.contract, batch_name=batch_name, source=source)
        passed = contract_report.passed and gx_report.passed
        fingerprint = self._fingerprint(frame)

        quarantine_path: Path | None = None
        if not passed:
            quarantine_path = self.quarantine_dir / f"{batch_name}.csv"
            frame.to_csv(quarantine_path, index=False)

        evidence_path = self.evidence_dir / f"{batch_name}_quality_report.json"
        payload = {
            "batch_name": batch_name,
            "source": source,
            "decision": "PASS" if passed else "BLOCK",
            "batch_fingerprint": fingerprint,
            "contract": contract_report.to_dict(),
            "great_expectations": gx_report.to_dict(),
            "quarantine_path": None if quarantine_path is None else str(quarantine_path),
        }
        evidence_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

        failed_rules = sorted(set(contract_report.failed_rule_ids + gx_report.failed_rule_ids))
        return GateDecision(
            batch_name=batch_name,
            source=source,
            decision="PASS" if passed else "BLOCK",
            contract_passed=contract_report.passed,
            gx_passed=gx_report.passed,
            failed_rule_ids=failed_rules,
            batch_fingerprint=fingerprint,
            evidence_path=str(evidence_path),
            quarantine_path=None if quarantine_path is None else str(quarantine_path),
        )

    @staticmethod
    def _fingerprint(frame: pd.DataFrame) -> str:
        canonical = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
