"""High-level Phase 5 workflow shared by CLI scripts and verification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from creditscore.utils.config import load_yaml
from creditscore.utils.hashing import file_sha256

from .audit_log import AuditLog
from .decision import GovernanceDecisionService
from .evaluator import GovernanceEvaluator
from .evidence import build_scenario_evidence
from .models import EvidenceBundle, GovernanceDecision
from .policy import GovernancePolicy
from .registry import ModelRegistry, ModelVersionRecord


class GovernanceWorkflow:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.config: dict[str, Any] = load_yaml(self.root / "configs" / "phase5.yaml")
        self.policy = GovernancePolicy.from_config(self.config)
        self.registry = ModelRegistry(self.root / self.config["paths"]["registry"])
        self.audit = AuditLog(self.root / self.config["paths"]["audit_log"])
        self.evaluator = GovernanceEvaluator(self.policy)
        self.service = GovernanceDecisionService(
            evaluator=self.evaluator,
            registry=self.registry,
            audit_log=self.audit,
            approved_stage=str(self.config["registry"]["approved_stage"]),
            rejected_stage=str(self.config["registry"]["rejected_stage"]),
        )

    @property
    def model_name(self) -> str:
        return str(self.config["registry"]["model_name"])

    def version_for(self, scenario: str) -> str:
        return str(self.config["scenarios"][scenario]["model_version"])

    def prepare_candidate(self, scenario: str) -> ModelVersionRecord:
        version = self.version_for(scenario)
        artifact_path = self.root / self.config["registry"]["artifact_path"]
        record = self.registry.register(
            model_name=self.model_name,
            version=version,
            artifact_path=str(artifact_path),
            artifact_sha256=file_sha256(artifact_path),
            metadata={"scenario": scenario, "source": self.config["scenarios"][scenario]["source"]},
        )
        if record.stage == "REGISTERED":
            self.audit.append("MODEL_REGISTERED", record.to_dict())
            record = self.registry.transition(
                model_name=self.model_name,
                version=version,
                target_stage=str(self.config["registry"]["candidate_stage"]),
            )
            self.audit.append("REGISTRY_TRANSITION", record.to_dict())
        if record.stage != "CANDIDATE":
            raise ValueError(
                f"Scenario {scenario} requires a CANDIDATE record; current stage is {record.stage}."
            )
        return record

    def build_evidence(self, scenario: str) -> EvidenceBundle:
        bundle = build_scenario_evidence(self.root, scenario)
        self.audit.append(
            "EVIDENCE_COLLECTED",
            {
                "scenario": scenario,
                "artifact_hashes": {artifact.name: artifact.sha256 for artifact in bundle.artifacts},
            },
        )
        return bundle

    def _save_decision(self, scenario: str, decision: GovernanceDecision) -> Path:
        output = self.root / self.config["paths"]["evidence_dir"] / scenario / "governance_decision.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(decision.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return output

    def evaluate_only(self, scenario: str) -> GovernanceDecision:
        record = self.prepare_candidate(scenario)
        evidence = self.build_evidence(scenario)
        decision = self.evaluator.evaluate(
            model_name=self.model_name,
            model_version=record.version,
            current_stage=record.stage,
            evidence=evidence,
        )
        self._save_decision(scenario, decision)
        self.audit.append("GOVERNANCE_EVALUATED", decision.to_dict())
        return decision

    def evaluate_and_apply(self, scenario: str) -> tuple[GovernanceDecision, str, EvidenceBundle]:
        self.prepare_candidate(scenario)
        evidence = self.build_evidence(scenario)
        decision, stage = self.service.evaluate_and_apply(
            model_name=self.model_name,
            model_version=self.version_for(scenario),
            evidence=evidence,
        )
        self._save_decision(scenario, decision)
        return decision, stage, evidence
