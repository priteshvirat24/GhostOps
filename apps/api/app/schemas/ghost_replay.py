from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ReplayStatus(str):
    PENDING = "PENDING"
    RECONSTRUCTING = "RECONSTRUCTING"
    SIMULATING = "SIMULATING"
    COMPARING = "COMPARING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ReplayMode(str):
    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"
    COUNTERFACTUAL_REPLAY = "COUNTERFACTUAL_REPLAY"
    MEMORY_VALIDATION = "MEMORY_VALIDATION"
    INFRASTRUCTURE_DRIFT_SIMULATION = "INFRASTRUCTURE_DRIFT_SIMULATION"

class ReplayRequest(BaseModel):
    mode: str = ReplayMode.HISTORICAL_REPLAY
    deterministic_seed: int = 42
    max_steps: int = 10
    counterfactual_parameters: Dict[str, Any] = Field(default_factory=dict)
    memory_ids: List[str] = Field(default_factory=list)

class SimulationState(BaseModel):
    resource_id: str
    state_attributes: Dict[str, Any] = Field(default_factory=dict)
    is_simulated: bool = True

class SimulationMutation(BaseModel):
    mutation_id: str
    replay_id: str
    resource_id: str
    action_type: str
    pre_state: Dict[str, Any] = Field(default_factory=dict)
    post_state: Dict[str, Any] = Field(default_factory=dict)
    simulated_only: bool = True
    reversible: bool = True
    mutation_hash: str

class ReplayStep(BaseModel):
    replay_step_id: str
    replay_id: str
    step_order: int
    agent_name: str
    action_type: str
    target_resource: str
    input_summary: str
    output_summary: str
    simulated_pre_state: Dict[str, Any] = Field(default_factory=dict)
    simulated_post_state: Dict[str, Any] = Field(default_factory=dict)
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: float
    status: str
    duration_ms: float

class ReplayDifference(BaseModel):
    difference_id: str
    replay_id: str
    category: str
    historical_value: Any
    predicted_value: Any
    severity: str
    explanation: str
    evidence_refs: List[str] = Field(default_factory=list)

class MemoryRegression(BaseModel):
    regression_id: str
    replay_id: str
    memory_id: str
    regression_type: str  # DIAGNOSIS_REGRESSION | REMEDIATION_REGRESSION | INFRASTRUCTURE_REGRESSION | OUTCOME_REGRESSION | EVIDENCE_REGRESSION
    previous_confidence: float
    observed_confidence: float
    score_delta: float
    explanation: str
    severity: str
    status: str

class ReplayScore(BaseModel):
    overall_score: float
    classification: str  # EXCELLENT | RELIABLE | DEGRADED | FAILED
    diagnosis_accuracy: float
    evidence_accuracy: float
    remediation_accuracy: float
    outcome_accuracy: float
    temporal_compatibility: float
    provenance_completeness: float

class ReplayScenario(BaseModel):
    scenario_id: str
    replay_id: str
    source_incident_id: str
    completeness_score: float
    infrastructure_state: Dict[str, Any] = Field(default_factory=dict)
    incident_state: Dict[str, Any] = Field(default_factory=dict)
    telemetry_state: Dict[str, Any] = Field(default_factory=dict)
    memory_context: List[Dict[str, Any]] = Field(default_factory=list)
    scenario_hash: str

class ReplayProvenance(BaseModel):
    replay_id: str
    source_incident_id: str
    source_execution_id: Optional[str] = None
    source_snapshot_id: Optional[str] = None
    memory_version: str
    mode: str
    deterministic_seed: int
    started_at: str
    completed_at: Optional[str] = None
    steps: List[ReplayStep] = Field(default_factory=list)
    differences: List[ReplayDifference] = Field(default_factory=list)
    regressions: List[MemoryRegression] = Field(default_factory=list)
    mutations: List[SimulationMutation] = Field(default_factory=list)

class ReplayResult(BaseModel):
    replay_id: str
    source_incident_id: str
    mode: str
    status: str
    score: ReplayScore
    predicted_outcome: str
    actual_outcome: str
    termination_reason: str
    steps_count: int
    differences_count: int
    regressions_count: int
    created_at: str

class ReplaySummary(BaseModel):
    total_replays: int
    successful_replays: int
    degraded_memories_count: int
    active_regressions_count: int
    average_score: float
    recent_replays: List[ReplayResult] = Field(default_factory=list)
