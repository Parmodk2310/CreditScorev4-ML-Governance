"""
Shadow and Canary Deployment Manager for CreditScoreV4.

Implements safe model rollout:
1. Shadow (0% traffic, logs predictions) → 7-14 days
2. Canary 10% → 24 hours → validate
3. Canary 50% → 48 hours → validate
4. Canary 100% → 72 hours → validate
5. Full production or auto-rollback
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

import numpy as np
import pandas as pd
from loguru import logger


class DeploymentStage(Enum):
    SHADOW = "shadow"
    CANARY_10 = "canary_10"
    CANARY_50 = "canary_50"
    CANARY_100 = "canary_100"
    PRODUCTION = "production"
    ROLLED_BACK = "rolled_back"


@dataclass
class DeploymentConfig:
    """Configuration for safe deployment."""
    
    # Stage durations
    shadow_duration_days: int = 14
    canary_10_duration_hours: int = 24
    canary_50_duration_hours: int = 48
    canary_100_duration_hours: int = 72
    
    # Traffic splits
    shadow_traffic_split: float = 0.0
    canary_10_traffic_split: float = 0.10
    canary_50_traffic_split: float = 0.50
    canary_100_traffic_split: float = 1.00
    
    # Success criteria
    max_auc_degradation: float = 0.02  # For canary_10
    max_auc_degradation_50: float = 0.01  # For canary_50
    max_auc_degradation_100: float = 0.005  # For canary_100
    
    # Auto-rollback triggers
    auto_rollback_auc_threshold: float = 0.76
    auto_rollback_fairness_threshold: float = 0.80
    auto_rollback_error_rate: float = 0.05
    
    # Model registry
    model_name: str = "creditscorev4"
    production_model_version: Optional[str] = None
    candidate_model_version: Optional[str] = None


class DeploymentManager:
    """
    Manages safe model deployment through shadow and canary stages.
    
    During the incident, this would have prevented the degraded model
    from reaching full production traffic.
    """
    
    def __init__(self, config: Optional[DeploymentConfig] = None):
        self.config = config or DeploymentConfig()
        self.current_stage: DeploymentStage = DeploymentStage.SHADOW
        self.stage_start_time: Optional[datetime] = None
        self.metrics_history: List[Dict[str, Any]] = []
        self.deployment_log: List[Dict[str, Any]] = []
    
    def start_shadow_deployment(self, model_version: str):
        """Begin shadow deployment of candidate model."""
        self.config.candidate_model_version = model_version
        self.current_stage = DeploymentStage.SHADOW
        self.stage_start_time = datetime.now(timezone.utc)
        
        self._log_event("shadow_started", {
            "model_version": model_version,
            "duration_days": self.config.shadow_duration_days,
        })
        
        logger.info(f"Started shadow deployment for model {model_version}")
    
    def evaluate_shadow_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Evaluate shadow deployment metrics.
        
        In shadow mode, we compare predictions without affecting users.
        """
        self.metrics_history.append({
            "stage": "shadow",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
        })
        
        # Shadow deployment: log and compare, don't block
        auc = metrics.get("auc", 0)
        fairness_di = metrics.get("disparate_impact", 1.0)
        
        passed = auc >= 0.78 and fairness_di >= 0.80
        
        self._log_event("shadow_evaluation", {
            "passed": passed,
            "auc": auc,
            "disparate_impact": fairness_di,
        })
        
        return passed
    
    def promote_to_canary(self, stage: DeploymentStage = DeploymentStage.CANARY_10):
        """Promote from shadow to canary stage."""
        if self.current_stage != DeploymentStage.SHADOW:
            raise ValueError(f"Cannot promote from {self.current_stage.value}")
        
        self.current_stage = stage
        self.stage_start_time = datetime.now(timezone.utc)
        
        traffic_split = {
            DeploymentStage.CANARY_10: self.config.canary_10_traffic_split,
            DeploymentStage.CANARY_50: self.config.canary_50_traffic_split,
            DeploymentStage.CANARY_100: self.config.canary_100_traffic_split,
        }.get(stage, 0)
        
        self._log_event("canary_started", {
            "stage": stage.value,
            "traffic_split": traffic_split,
            "model_version": self.config.candidate_model_version,
        })
        
        logger.info(f"Promoted to {stage.value} with {traffic_split*100}% traffic")
    
    def evaluate_canary_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate canary deployment metrics and determine next action.
        
        Returns:
            Dict with 'action' (promote/rollback/hold) and 'reason'.
        """
        self.metrics_history.append({
            "stage": self.current_stage.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
        })
        
        auc = metrics.get("auc", 0)
        fairness_di = metrics.get("disparate_impact", 1.0)
        error_rate = metrics.get("error_rate", 0)
        
        # Check auto-rollback triggers
        if auc < self.config.auto_rollback_auc_threshold:
            return self._trigger_rollback(f"AUC {auc} below threshold {self.config.auto_rollback_auc_threshold}")
        
        if fairness_di < self.config.auto_rollback_fairness_threshold:
            return self._trigger_rollback(f"Disparate Impact {fairness_di} below threshold {self.config.auto_rollback_fairness_threshold}")
        
        if error_rate > self.config.auto_rollback_error_rate:
            return self._trigger_rollback(f"Error rate {error_rate} above threshold {self.config.auto_rollback_error_rate}")
        
        # Check stage-specific criteria
        stage_duration = datetime.now(timezone.utc) - self.stage_start_time
        
        if self.current_stage == DeploymentStage.CANARY_10:
            # Check AUC degradation
            auc_degradation = metrics.get("auc_degradation", 0)
            if auc_degradation > self.config.max_auc_degradation:
                return self._trigger_rollback(f"AUC degradation {auc_degradation} exceeds {self.config.max_auc_degradation}")
            
            # Check minimum duration
            if stage_duration >= timedelta(hours=self.config.canary_10_duration_hours):
                return {"action": "promote", "reason": "Canary 10% passed, promote to 50%", "next_stage": DeploymentStage.CANARY_50.value}
            
            return {"action": "hold", "reason": f"Canary 10% running ({stage_duration.total_seconds()/3600:.1f}h elapsed)"}
        
        elif self.current_stage == DeploymentStage.CANARY_50:
            auc_degradation = metrics.get("auc_degradation", 0)
            if auc_degradation > self.config.max_auc_degradation_50:
                return self._trigger_rollback(f"AUC degradation {auc_degradation} exceeds {self.config.max_auc_degradation_50}")
            
            if stage_duration >= timedelta(hours=self.config.canary_50_duration_hours):
                return {"action": "promote", "reason": "Canary 50% passed, promote to 100%", "next_stage": DeploymentStage.CANARY_100.value}
            
            return {"action": "hold", "reason": f"Canary 50% running ({stage_duration.total_seconds()/3600:.1f}h elapsed)"}
        
        elif self.current_stage == DeploymentStage.CANARY_100:
            auc_degradation = metrics.get("auc_degradation", 0)
            if auc_degradation > self.config.max_auc_degradation_100:
                return self._trigger_rollback(f"AUC degradation {auc_degradation} exceeds {self.config.max_auc_degradation_100}")
            
            if stage_duration >= timedelta(hours=self.config.canary_100_duration_hours):
                return {"action": "promote", "reason": "Canary 100% passed, promote to production", "next_stage": DeploymentStage.PRODUCTION.value}
            
            return {"action": "hold", "reason": f"Canary 100% running ({stage_duration.total_seconds()/3600:.1f}h elapsed)"}
        
        return {"action": "unknown", "reason": f"Unknown stage: {self.current_stage.value}"}
    
    def _trigger_rollback(self, reason: str) -> Dict[str, Any]:
        """Trigger automatic rollback."""
        self.current_stage = DeploymentStage.ROLLED_BACK
        self._log_event("rollback_triggered", {"reason": reason})
        
        logger.critical(f"AUTO-ROLLBACK TRIGGERED: {reason}")
        
        return {
            "action": "rollback",
            "reason": reason,
            "previous_production_version": self.config.production_model_version,
        }
    
    def promote_to_production(self):
        """Complete deployment to production."""
        self.config.production_model_version = self.config.candidate_model_version
        self.current_stage = DeploymentStage.PRODUCTION
        
        self._log_event("production_promotion", {
            "model_version": self.config.candidate_model_version,
        })
        
        logger.info(f"Model {self.config.candidate_model_version} promoted to production")
    
    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log deployment event."""
        self.deployment_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "stage": self.current_stage.value,
            "details": details,
        })
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        stage_duration = (
            datetime.now(timezone.utc) - self.stage_start_time
            if self.stage_start_time else timedelta(0)
        )
        
        return {
            "current_stage": self.current_stage.value,
            "candidate_version": self.config.candidate_model_version,
            "production_version": self.config.production_model_version,
            "stage_duration_hours": stage_duration.total_seconds() / 3600,
            "metrics_history_count": len(self.metrics_history),
            "recent_events": self.deployment_log[-5:],
        }
    
    def save_state(self, path: str):
        """Save deployment state to file."""
        state = {
            "config": {
                "model_name": self.config.model_name,
                "production_version": self.config.production_model_version,
                "candidate_version": self.config.candidate_model_version,
            },
            "current_stage": self.current_stage.value,
            "stage_start_time": self.stage_start_time.isoformat() if self.stage_start_time else None,
            "metrics_history": self.metrics_history,
            "deployment_log": self.deployment_log,
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"Saved deployment state to {path}")
    
    @classmethod
    def load_state(cls, path: str) -> "DeploymentManager":
        """Load deployment state from file."""
        with open(path, "r") as f:
            state = json.load(f)
        
        config = DeploymentConfig(
            model_name=state["config"]["model_name"],
            production_model_version=state["config"].get("production_version"),
            candidate_model_version=state["config"].get("candidate_version"),
        )
        
        manager = cls(config)
        manager.current_stage = DeploymentStage(state["current_stage"])
        manager.stage_start_time = (
            datetime.fromisoformat(state["stage_start_time"])
            if state["stage_start_time"] else None
        )
        manager.metrics_history = state.get("metrics_history", [])
        manager.deployment_log = state.get("deployment_log", [])
        
        return manager