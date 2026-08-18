from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from ghostops_shared import IncidentSeverity, IncidentStatus, RemediationStatus

class AgentState(BaseModel):
    """
    Unified typed state graph context passed between LangGraph / Orchestrator state nodes.
    Supports budget counters, hypotheses competition, 9-dimension temporal comparisons,
    remediation applicability, agent disagreements, and trace step executions.
    """
    run_id: str = Field(default_factory=lambda: "run-default")
    incident_id: Optional[str] = None
    thread_id: str = Field(default_factory=lambda: "thread-default")
    current_node: str = "supervisor"

    # Budget Limits & Progress Counters
    step_count: int = 0
    max_steps: int = 20
    retrieval_rounds: int = 0
    max_retrieval_rounds: int = 3
    reflection_rounds: int = 0
    max_reflection_rounds: int = 2
    termination_reason: Optional[str] = None

    # Telemetry & Current Snapshot
    raw_events: List[Dict[str, Any]] = Field(default_factory=list)
    target_resource_id: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    current_snapshot: Optional[Dict[str, Any]] = None

    # Historian & Memory Candidates
    retrieved_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    selected_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    historical_snapshots: List[Dict[str, Any]] = Field(default_factory=list)
    historical_evidence: List[Dict[str, Any]] = Field(default_factory=list)

    # Investigator Hypotheses & Evidence References
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    investigation_findings: Optional[str] = None
    timeline: List[Dict[str, Any]] = Field(default_factory=list)

    # Temporal Infrastructure Comparison & Remediation Applicability
    temporal_comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    remediation_applicability: Optional[Dict[str, Any]] = None
    infra_drift_detected: bool = False

    # Validation, Reflection & Confidence
    confidence: float = 0.5
    uncertainty: Optional[str] = None
    critic_feedback: Optional[Dict[str, Any]] = None
    agent_disagreements: List[Dict[str, Any]] = Field(default_factory=list)
    validation_passed: bool = False
    validation_reasons: List[str] = Field(default_factory=list)

    # Tool Results & Execution Traces
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    trace_steps: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class AgentNode(BaseModel):
    name: str
    description: str

    def execute(self, state: AgentState) -> AgentState:
        """Execute node step and update AgentState graph context."""
        raise NotImplementedError
