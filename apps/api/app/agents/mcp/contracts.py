from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class MCPToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    read_only: bool = True
    requires_approval: bool = False
    risk_level: str = "L0"  # L0, L1, L2, L3, L4, L5

class MCPToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    agent_id: str
    incident_id: Optional[str] = None
    idempotency_key: str
    saga_id: Optional[str] = None

class MCPToolResponse(BaseModel):
    success: bool
    tool_name: str
    request_id: str
    idempotency_key: str
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    evidence_refs: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TemporalVerdict(BaseModel):
    historical_fix: str
    historical_validity: bool
    current_environment_match: float
    dimension_diffs: List[Dict[str, Any]] = Field(default_factory=list)
    risk: str  # low | medium | high | critical
    recommendation: str  # applicable | do_not_execute | conditional
    reason: str
    confidence: float = 0.85

class ValidationResult(BaseModel):
    status: str  # pass | fail | needs_human
    risk_tier: str  # L0 to L5
    blast_radius: str
    sandbox_proven: bool = False
    sandbox_evidence: Optional[Dict[str, Any]] = None
    policy_violations: List[str] = Field(default_factory=list)
    requires_second_reviewer: bool = False
    reason: str

class VerificationResult(BaseModel):
    overall_status: str  # verified | provisionally_successful | failed
    signal_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    # e.g., {"metrics": {"status": "PASS", "latency_recovered": True}, "error_rate": {"status": "PASS", "drop_pct": 98.2}}
    side_effects_detected: bool = False
    confidence: float = 0.90
    trust_delta: float = 0.0
