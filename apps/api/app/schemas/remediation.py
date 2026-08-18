from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from ghostops_shared import RemediationStatus

class PlanStepSchema(BaseModel):
    step_order: int
    action_type: str
    target_resource_arn: str
    parameters: Dict[str, Any] = {}
    rollback_parameters: Dict[str, Any] = {}
    status: str = "PENDING"
    execution_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RemediationPlanResponse(BaseModel):
    id: str
    incident_id: str
    title: str
    explanation: str
    status: RemediationStatus
    idempotency_key: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    estimated_risk: str
    requires_human_approval: bool
    steps: List[PlanStepSchema] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PlanApprovalRequest(BaseModel):
    approved_by: str
    approved: bool
    rejection_reason: Optional[str] = None
