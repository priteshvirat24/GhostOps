from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from ghostops_shared import RemediationStatus

class ActionSafetyLevel(str):
    READ_ONLY = "READ_ONLY"
    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"

class BlastRadius(str):
    LOCAL = "LOCAL"
    SERVICE = "SERVICE"
    CLUSTER = "CLUSTER"
    REGION = "REGION"
    GLOBAL = "GLOBAL"

class RemediationActionType(str):
    UPDATE_CONFIGURATION = "UPDATE_CONFIGURATION"
    SCALE_RESOURCE = "SCALE_RESOURCE"
    RESTART_SERVICE = "RESTART_SERVICE"
    ROTATE_CONFIGURATION = "ROTATE_CONFIGURATION"
    CHANGE_SECURITY_RULE = "CHANGE_SECURITY_RULE"
    ROLLBACK_DEPLOYMENT = "ROLLBACK_DEPLOYMENT"
    REVERT_CONFIGURATION = "REVERT_CONFIGURATION"
    ADJUST_CONNECTION_POOL = "ADJUST_CONNECTION_POOL"
    DRAIN_RESOURCE = "DRAIN_RESOURCE"

class VerificationCheck(BaseModel):
    check_id: str
    type: str
    target: str
    expected_condition: str
    timeout_seconds: int = 300
    evidence_refs: List[str] = Field(default_factory=list)

class RollbackAction(BaseModel):
    action_type: str
    target_resource_arn: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str = "Rollback previous remediation action"

class PlanStepPayload(BaseModel):
    step_order: int
    action_type: str
    target_resource_arn: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str
    evidence_refs: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"
    requires_approval: bool = False
    idempotency_key: str
    preconditions: List[str] = Field(default_factory=list)
    expected_effect: str
    failure_conditions: List[str] = Field(default_factory=list)
    rollback_action: Optional[RollbackAction] = None
    verification_requirements: List[VerificationCheck] = Field(default_factory=list)
    status: str = "PENDING"

class RecommendedAction(BaseModel):
    action_id: str = Field(default="act-1")
    action_type: str
    target: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str
    historical_precedent_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    risk_level: str = "MEDIUM_RISK"
    expected_effect: str = "Restore service stability"
    preconditions: List[str] = Field(default_factory=list)
    failure_conditions: List[str] = Field(default_factory=list)
    rollback_action: Optional[RollbackAction] = None
    verification_requirements: List[VerificationCheck] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
        "extra": "ignore"
    }

class RootCauseSummary(BaseModel):
    statement: str
    hypothesis_id: str = "H1"
    evidence_ids: List[str] = Field(default_factory=list)

class PlannerProposalOutput(BaseModel):
    plan_title: str
    explanation: str
    root_cause: RootCauseSummary
    recommended_actions: List[RecommendedAction] = Field(default_factory=list)
    confidence: float = 0.5
    temporal_compatibility: float = 0.0
    requires_human_approval: bool = True
    validation_requirements: List[VerificationCheck] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
    status: str = "PROPOSED"  # PROPOSED | REJECTED

    model_config = {
        "populate_by_name": True,
        "extra": "ignore"
    }

class RiskAssessment(BaseModel):
    risk_level: str  # READ_ONLY | LOW_RISK | MEDIUM_RISK | HIGH_RISK | CRITICAL
    risk_score: float  # 0.0 to 1.0
    blast_radius: str  # LOCAL | SERVICE | CLUSTER | REGION | GLOBAL
    factors: List[str] = Field(default_factory=list)

class SafetyCheckResult(BaseModel):
    passed: bool
    check_name: str
    severity: str = "HIGH"  # LOW | MEDIUM | HIGH | CRITICAL
    message: str
    evidence_refs: List[str] = Field(default_factory=list)
    blocking: bool = True

class ApprovalGate(BaseModel):
    approval_id: str
    plan_id: str
    required: bool = True
    required_approver_role: str = "DevOpsLead"
    status: str = "PENDING"  # NOT_REQUIRED | PENDING | APPROVED | REJECTED | EXPIRED
    requested_at: str
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    confirmation_text: Optional[str] = None
    expires_at: str

class ApprovalDecisionPayload(BaseModel):
    approved_by: str = "DevOpsLead"
    confirmation_text: Optional[str] = None

class RejectionPayload(BaseModel):
    rejected_by: str = "DevOpsLead"
    rejection_reason: str

class RemediationPlanResponse(BaseModel):
    plan_id: str
    incident_id: str
    investigation_run_id: str
    version: int = 1
    title: str
    summary: str
    status: RemediationStatus
    root_cause_hypothesis_id: str
    confidence: float
    compatibility_score: float
    compatibility_classification: str
    risk: RiskAssessment
    steps: List[PlanStepPayload] = Field(default_factory=list)
    approval_gate: ApprovalGate
    safety_checks: List[SafetyCheckResult] = Field(default_factory=list)
    rollback_plan: List[RollbackAction] = Field(default_factory=list)
    verification_plan: List[VerificationCheck] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    historical_precedent_refs: List[str] = Field(default_factory=list)
    created_at: str
    expires_at: str

class ValidationStatusResponse(BaseModel):
    plan_id: str
    valid: bool
    status: str
    safety_checks: List[SafetyCheckResult]
    drift_detected: bool = False
    conflict_detected: bool = False
    expired: bool = False
    message: str
