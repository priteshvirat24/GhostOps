from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ExecutionStatus(str):
    PENDING = "PENDING"
    PRECHECKING = "PRECHECKING"
    READY = "READY"
    EXECUTING = "EXECUTING"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"

class StepExecutionStatus(str):
    PENDING = "PENDING"
    PRECHECKING = "PRECHECKING"
    READY = "READY"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    COMPENSATING = "COMPENSATING"
    COMPENSATED = "COMPENSATED"
    COMPENSATION_FAILED = "COMPENSATION_FAILED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"

class LockStatus(str):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"

class ExecutionPrecheckResult(BaseModel):
    passed: bool
    check_name: str
    severity: str = "HIGH"  # LOW | MEDIUM | HIGH | CRITICAL
    message: str
    blocking: bool = True
    evidence_refs: List[str] = Field(default_factory=list)

class ExecutionRequestPayload(BaseModel):
    dry_run: bool = False
    requested_by: str = "DevOpsLead"
    force_real_aws: bool = False

class DryRunResponse(BaseModel):
    dry_run: bool = True
    would_execute: bool
    plan_id: str
    plan_version: int
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    expected_pre_state: Dict[str, Any] = Field(default_factory=dict)
    expected_post_state: Dict[str, Any] = Field(default_factory=dict)
    rollback_plan: List[Dict[str, Any]] = Field(default_factory=list)
    verification_plan: List[Dict[str, Any]] = Field(default_factory=list)
    risk: Dict[str, Any] = Field(default_factory=dict)
    blocking_conditions: List[str] = Field(default_factory=list)

class ExecutionStepDetail(BaseModel):
    execution_step_id: str
    step_order: int
    action_type: str
    target_resource: str
    execution_mode: str = "MOCK"
    status: str
    idempotency_key: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    attempt_count: int = 1
    request_id: Optional[str] = None
    result_summary: Optional[str] = None
    failure_reason: Optional[str] = None
    pre_state: Dict[str, Any] = Field(default_factory=dict)
    post_state: Dict[str, Any] = Field(default_factory=dict)
    compensation_status: str = "PENDING"
    verification_status: str = "PENDING"

class ExecutionEventPayload(BaseModel):
    event_id: str
    execution_id: str
    step_id: Optional[str] = None
    event_type: str
    timestamp: str
    actor: str = "GhostOps.SagaEngine"
    request_id: Optional[str] = None
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "INFO"

class ExecutionDetailResponse(BaseModel):
    execution_id: str
    plan_id: str
    plan_version: int
    incident_id: str
    status: str
    execution_mode: str = "MOCK"
    started_at: str
    completed_at: Optional[str] = None
    failure_reason: Optional[str] = None
    termination_reason: str = "IN_PROGRESS"
    current_step: int = 1
    executed_steps: int = 0
    compensated_steps: int = 0
    verification_status: str = "PENDING"
    incident_recovery_status: str = "UNKNOWN"  # RECOVERED | PERSISTS | UNKNOWN
    lock_id: Optional[str] = None
    executor: str = "GhostOps.SagaEngine"
    trace_id: str
    steps_detail: List[ExecutionStepDetail] = Field(default_factory=list)
    events: List[ExecutionEventPayload] = Field(default_factory=list)
    created_at: str
    updated_at: str
