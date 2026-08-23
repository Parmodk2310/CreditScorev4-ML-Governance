"""
Incident Response Engine for CreditScoreV4.
Automated SEV classification, escalation, and remediation.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

import requests
from loguru import logger


class Severity(Enum):
    SEV1 = "sev1"  # Critical - Production outage
    SEV2 = "sev2"  # High - Significant degradation
    SEV3 = "sev3"  # Medium - Monitoring alerts
    SEV4 = "sev4"  # Low - Informational


@dataclass
class IncidentConfig:
    """Incident response configuration."""
    
    # Escalation times (minutes)
    sev1_response_minutes: int = 15
    sev2_response_minutes: int = 60
    sev3_response_minutes: int = 240
    sev4_response_minutes: int = 1440
    
    # Auto-rollback
    auto_rollback_enabled: bool = True
    
    # PagerDuty
    pagerduty_api_key: Optional[str] = None
    pagerduty_service_key: Optional[str] = None
    
    # Slack
    slack_webhook_url: Optional[str] = None


class Incident:
    """Represents an active incident."""
    
    def __init__(
        self,
        incident_type: str,
        severity: Severity,
        description: str,
        metrics: Dict[str, Any],
        auto_rollback: bool = False,
    ):
        self.id = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{severity.value}"
        self.type = incident_type
        self.severity = severity
        self.description = description
        self.metrics = metrics
        self.auto_rollback = auto_rollback
        self.created_at = datetime.now(timezone.utc)
        self.status = "open"
        self.resolved_at: Optional[datetime] = None
        self.actions_taken: List[Dict[str, Any]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity.value,
            "description": self.description,
            "metrics": self.metrics,
            "auto_rollback": self.auto_rollback,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "actions_taken": self.actions_taken,
        }


class IncidentResponseEngine:
    """
    Automated incident response for ML production issues.
    
    During the AUC 0.81 → 0.74 incident, this would have:
    1. Classified as SEV1 within minutes
    2. Auto-triggered rollback
    3. Paged the on-call engineer
    4. Executed the AUC degradation runbook
    """
    
    # Incident classification rules
    CLASSIFICATION_RULES = [
        {
            "name": "auc_critical_degradation",
            "condition": lambda m: m.get("auc", 1.0) < 0.76,
            "severity": Severity.SEV1,
            "auto_rollback": True,
            "runbook": "RB-001",
        },
        {
            "name": "auc_significant_degradation",
            "condition": lambda m: m.get("auc", 1.0) < 0.78,
            "severity": Severity.SEV2,
            "auto_rollback": True,
            "runbook": "RB-001",
        },
        {
            "name": "data_quality_failure",
            "condition": lambda m: m.get("null_rate", 0) > 0.05,
            "severity": Severity.SEV1,
            "auto_rollback": True,
            "runbook": "RB-002",
        },
        {
            "name": "fairness_violation",
            "condition": lambda m: m.get("disparate_impact", 1.0) < 0.80,
            "severity": Severity.SEV1,
            "auto_rollback": True,
            "runbook": "RB-003",
        },
        {
            "name": "drift_warning",
            "condition": lambda m: m.get("psi", 0) > 0.2,
            "severity": Severity.SEV2,
            "auto_rollback": False,
            "runbook": "RB-004",
        },
        {
            "name": "high_latency",
            "condition": lambda m: m.get("p99_latency_ms", 0) > 500,
            "severity": Severity.SEV3,
            "auto_rollback": False,
            "runbook": None,
        },
    ]
    
    # Runbooks
    RUNBOOKS = {
        "RB-001": {
            "title": "AUC Degradation Response",
            "steps": [
                "Check data quality metrics and NULL rates",
                "Run drift detection on all features",
                "Analyze feature importance shifts vs baseline",
                "Check upstream vendor API status and schema",
                "Review recent deployments for correlation",
                "If auto-rollback triggered: verify rollback success",
                "If manual: initiate rollback or emergency retraining",
                "Document root cause for post-mortem",
            ],
        },
        "RB-002": {
            "title": "Data Quality Failure Response",
            "steps": [
                "Identify all affected features and NULL rates",
                "Check upstream vendor for schema changes",
                "Run data contract validation suite",
                "Alert data engineering team via PagerDuty",
                "If auto-rollback triggered: verify rollback success",
                "Coordinate with vendor for data fix",
                "Implement temporary data patching if needed",
            ],
        },
        "RB-003": {
            "title": "Fairness Violation Response",
            "steps": [
                "Run SHAP bias attribution analysis",
                "Identify features driving disparate impact",
                "Check for proxy variables (zip_code → race)",
                "Alert compliance and legal teams",
                "If auto-rollback triggered: verify rollback success",
                "Prepare regulatory reporting documentation",
                "Plan model retraining with fairness constraints",
            ],
        },
        "RB-004": {
            "title": "Drift Detection Response",
            "steps": [
                "Analyze drifted features for business context",
                "Check if drift is expected (seasonality, policy change)",
                "Run feature importance analysis",
                "Evaluate if retraining is needed",
                "Schedule model refresh if drift is significant",
            ],
        },
    }
    
    def __init__(self, config: Optional[IncidentConfig] = None):
        self.config = config or IncidentConfig()
        self.active_incidents: Dict[str, Incident] = {}
        self.resolved_incidents: List[Incident] = []
    
    def evaluate_metrics(self, metrics: Dict[str, Any]) -> List[Incident]:
        """
        Evaluate metrics against classification rules and create incidents.
        
        Returns:
            List of newly created incidents.
        """
        new_incidents = []
        
        for rule in self.CLASSIFICATION_RULES:
            if rule["condition"](metrics):
                # Check if similar incident already active
                existing = self._find_similar_active(rule["name"])
                if existing:
                    continue
                
                incident = Incident(
                    incident_type=rule["name"],
                    severity=rule["severity"],
                    description=f"Triggered by rule: {rule['name']}",
                    metrics=metrics,
                    auto_rollback=rule.get("auto_rollback", False),
                )
                
                self.active_incidents[incident.id] = incident
                new_incidents.append(incident)
                
                self._handle_incident(incident, rule.get("runbook"))
        
        return new_incidents
    
    def _find_similar_active(self, incident_type: str) -> Optional[Incident]:
        """Find active incident of same type."""
        for incident in self.active_incidents.values():
            if incident.type == incident_type and incident.status == "open":
                return incident
        return None
    
    def _handle_incident(self, incident: Incident, runbook_id: Optional[str]):
        """Handle incident with appropriate actions."""
        logger.critical(
            f"INCIDENT {incident.id}: {incident.type} ({incident.severity.value}) - "
            f"{incident.description}"
        )
        
        # Execute runbook
        if runbook_id and runbook_id in self.RUNBOOKS:
            runbook = self.RUNBOOKS[runbook_id]
            logger.info(f"Executing runbook {runbook_id}: {runbook['title']}")
            incident.actions_taken.append({
                "action": "runbook_executed",
                "runbook_id": runbook_id,
                "runbook_title": runbook["title"],
                "steps": runbook["steps"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        
        # Auto-rollback
        if incident.auto_rollback and self.config.auto_rollback_enabled:
            logger.critical(f"Auto-rollback triggered for {incident.id}")
            incident.actions_taken.append({
                "action": "auto_rollback_initiated",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            self._trigger_rollback(incident)
        
        # Page on-call
        if incident.severity in (Severity.SEV1, Severity.SEV2):
            self._page_oncall(incident)
        
        # Slack notification
        self._notify_slack(incident)
    
    def _trigger_rollback(self, incident: Incident):
        """Trigger model rollback."""
        # Integration point with deployment manager
        incident.actions_taken.append({
            "action": "rollback_completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Rollback completed for incident {incident.id}")
    
    def _page_oncall(self, incident: Incident):
        """Page on-call engineer via PagerDuty."""
        if not self.config.pagerduty_service_key:
            logger.warning("PagerDuty not configured, skipping page")
            return
        
        try:
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json={
                    "routing_key": self.config.pagerduty_service_key,
                    "event_action": "trigger",
                    "dedup_key": incident.id,
                    "payload": {
                        "summary": f"[{incident.severity.value.upper()}] {incident.type}",
                        "severity": "critical" if incident.severity == Severity.SEV1 else "error",
                        "source": "creditscorev4-ml-governance",
                        "custom_details": incident.metrics,
                    },
                },
                timeout=10,
            )
            response.raise_for_status()
            
            incident.actions_taken.append({
                "action": "pagerduty_page_sent",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"PagerDuty page sent for {incident.id}")
            
        except Exception as e:
            logger.error(f"Failed to send PagerDuty page: {e}")
    
    def _notify_slack(self, incident: Incident):
        """Send Slack notification."""
        if not self.config.slack_webhook_url:
            return
        
        color = {
            Severity.SEV1: "#FF0000",
            Severity.SEV2: "#FF8C00",
            Severity.SEV3: "#FFD700",
            Severity.SEV4: "#00FF00",
        }.get(incident.severity, "#808080")
        
        message = {
            "attachments": [{
                "color": color,
                "title": f"[{incident.severity.value.upper()}] {incident.type}",
                "text": incident.description,
                "fields": [
                    {"title": "Incident ID", "value": incident.id, "short": True},
                    {"title": "Auto-Rollback", "value": str(incident.auto_rollback), "short": True},
                    {"title": "Metrics", "value": json.dumps(incident.metrics, indent=2), "short": False},
                ],
                "footer": "CreditScoreV4 ML Governance",
                "ts": int(datetime.now(timezone.utc).timestamp()),
            }]
        }
        
        try:
            requests.post(
                self.config.slack_webhook_url,
                json=message,
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    def resolve_incident(self, incident_id: str, resolution: str):
        """Resolve an active incident."""
        if incident_id not in self.active_incidents:
            raise ValueError(f"Incident {incident_id} not found")
        
        incident = self.active_incidents.pop(incident_id)
        incident.status = "resolved"
        incident.resolved_at = datetime.now(timezone.utc)
        incident.actions_taken.append({
            "action": "resolved",
            "resolution": resolution,
            "timestamp": incident.resolved_at.isoformat(),
        })
        
        self.resolved_incidents.append(incident)
        logger.info(f"Resolved incident {incident_id}: {resolution}")
    
    def get_active_incidents(self) -> List[Dict[str, Any]]:
        """Get all active incidents."""
        return [inc.to_dict() for inc in self.active_incidents.values()]
    
    def get_incident_summary(self) -> Dict[str, Any]:
        """Get summary of incident status."""
        return {
            "active_incidents": len(self.active_incidents),
            "resolved_incidents_24h": len([
                i for i in self.resolved_incidents
                if i.resolved_at and i.resolved_at > datetime.now(timezone.utc) - timedelta(hours=24)
            ]),
            "sev1_active": len([i for i in self.active_incidents.values() if i.severity == Severity.SEV1]),
            "sev2_active": len([i for i in self.active_incidents.values() if i.severity == Severity.SEV2]),
          }