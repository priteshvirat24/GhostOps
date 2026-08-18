from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum

class CounterfactualReplayVerdict(str, Enum):
    REPLAY_SAME = "REPLAY_SAME"
    REPLAY_DIFFERENT = "REPLAY_DIFFERENT"
    CORRECTLY_REJECTED = "CORRECTLY_REJECTED"
    UNSAFE_REPLAY = "UNSAFE_REPLAY"
    INCONCLUSIVE = "INCONCLUSIVE"

class EvaluationCaseContract(BaseModel):
    benchmark_id: str
    incident_id: str
    case_category: str  # applicable_success | obsolete_drift | historical_failure | contradictory_evidence | low_confidence | negative_memory | adversarial_injection
    dataset_split: str = "development" # development | validation | holdout
    corpus_version: str = "ghostops-history-v1"
    service: str
    region: str = "us-east-1"
    symptom: str
    incident_title: str
    incident_description: str
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    infrastructure_snapshot: Dict[str, Any] = Field(default_factory=dict)
    
    # Ground Truth Expectations
    expected_root_cause: str
    expected_precedent_id: Optional[str] = None
    expected_temporal_verdict: str # APPLICABLE | DO_NOT_EXECUTE | CAUTION_DRIFT
    expected_safety_outcome: str # EXECUTE | REJECT | DO_NOT_EXECUTE
    expected_risk_level: str = "LOW"
    historical_action_taken: str
    historical_result: str # SUCCESS | FAILED | OUTDATED

class EvaluationCaseResultResponse(BaseModel):
    case_id: str
    benchmark_id: str
    incident_id: str
    case_category: str
    expected_root_cause: str
    actual_hypothesis: str
    expected_precedent_id: Optional[str] = None
    retrieved_precedent_id: Optional[str] = None
    retrieval_rank: Optional[int] = None
    retrieval_score: float = 0.0
    expected_temporal_verdict: str
    actual_temporal_verdict: str
    expected_safety_outcome: str
    actual_safety_outcome: str
    decision_match: bool
    safety_match: bool
    would_execute: bool
    unsafe_execution: bool
    evidence_grounding_score: float
    counterfactual_status: str
    trace_details: Dict[str, Any] = Field(default_factory=dict)

class EvaluationRunResponse(BaseModel):
    evaluation_run_id: str
    dataset_version: str
    status: str
    total_cases: int
    precision_at_1: float
    precision_at_3: float
    mrr: float
    temporal_verdict_accuracy: float
    evidence_grounding_score: float
    unsafe_replay_rate: float
    false_execution_rate: float
    regression_gate_passed: bool
    gate_details: Dict[str, Any] = Field(default_factory=dict)
    summary: str
    duration_ms: float
    started_at: str
    completed_at: Optional[str] = None
    cases: List[EvaluationCaseResultResponse] = Field(default_factory=list)
