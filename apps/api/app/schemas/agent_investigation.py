from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class EvidenceCitation(BaseModel):
    source: str = "incident_evidence"
    record_id: str
    claim: str

class Hypothesis(BaseModel):
    hypothesis_id: str = Field(default="H1")
    statement: str
    evidence: List[EvidenceCitation] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    confidence: float = 0.5
    status: str = "PLAUSIBLE"  # SUPPORTED | PLAUSIBLE | CONTRADICTED | UNKNOWN
    next_question: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "extra": "ignore"
    }

    def __init__(self, **data: Any):
        if "id" in data and "hypothesis_id" not in data:
            data["hypothesis_id"] = data["id"]
        if "counter_evidence" in data and "contradicting_evidence" not in data:
            data["contradicting_evidence"] = data["counter_evidence"]
        super().__init__(**data)
        if self.evidence and not self.supporting_evidence:
            self.supporting_evidence = [e.record_id for e in self.evidence]
        elif self.supporting_evidence and not self.evidence:
            self.evidence = [EvidenceCitation(source="incident_evidence", record_id=ref, claim=f"Cited evidence {ref}") for ref in self.supporting_evidence]

class InvestigatorAnalysisOutput(BaseModel):
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    selected_hypothesis: str = "H1"
    disagreement_flag: bool = False
    confidence: float = 0.5
    next_retrieval_query: Optional[str] = None
    reasoning_summary: Optional[str] = None
    validation_errors: List[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
        "extra": "ignore"
    }

class TemporalComparisonDimension(BaseModel):
    dimension: str
    historical_value: Any
    current_value: Any
    match: bool
    impact: str = "MEDIUM"  # LOW | MEDIUM | HIGH | CRITICAL
    confidence: float = 1.0
    evidence_refs: List[str] = Field(default_factory=list)

class RemediationApplicability(BaseModel):
    historical_incident_id: str
    successful_action: Optional[Dict[str, Any]] = None
    failed_preceding_actions: List[Dict[str, Any]] = Field(default_factory=list)
    compatibility_score: float = 0.0
    classification: str = "UNKNOWN"  # HIGHLY_COMPATIBLE | COMPATIBLE_WITH_DIFFERENCES | LOW_COMPATIBILITY | INAPPLICABLE | UNKNOWN
    supporting_differences: List[str] = Field(default_factory=list)
    blocking_differences: List[str] = Field(default_factory=list)
    confidence: float = 0.5
    evidence_refs: List[str] = Field(default_factory=list)

class CritiqueResult(BaseModel):
    approved: bool = True
    issues: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    confidence_adjustment: float = 0.0
    recommended_next_step: str = "CONTINUE"

class AgentDisagreement(BaseModel):
    disagreement_id: str
    run_id: str
    agent_a: str
    agent_b: str
    position_a: str
    position_b: str
    evidence_refs: List[str] = Field(default_factory=list)
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    confidence: float = 0.5

class InvestigationRequestPayload(BaseModel):
    max_steps: int = 20
    max_retrieval_rounds: int = 3
    max_reflection_rounds: int = 2

class InvestigationResponse(BaseModel):
    run_id: str
    incident_id: str
    status: str
    selected_hypothesis: Optional[Hypothesis] = None
    confidence: float = 0.5
    historical_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    temporal_comparisons: List[TemporalComparisonDimension] = Field(default_factory=list)
    remediation_applicability: Optional[RemediationApplicability] = None
    agent_disagreements: List[AgentDisagreement] = Field(default_factory=list)
    termination_reason: str

class StepTraceItem(BaseModel):
    step_id: str
    agent_name: str
    input_summary: str
    output_summary: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    confidence: float
    duration_ms: float
    timestamp: str

class TraceDetailResponse(BaseModel):
    run_id: str
    incident_id: str
    status: str
    agent_steps: List[StepTraceItem] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_progression: List[Dict[str, Any]] = Field(default_factory=list)
    disagreements: List[AgentDisagreement] = Field(default_factory=list)
    termination_reason: str
