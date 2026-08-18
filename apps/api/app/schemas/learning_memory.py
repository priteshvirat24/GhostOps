from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class OutcomeClassification(str):
    COMPLETED_AND_RECOVERED = "COMPLETED_AND_RECOVERED"
    COMPLETED_BUT_INCIDENT_PERSISTS = "COMPLETED_BUT_INCIDENT_PERSISTS"
    ROLLED_BACK_AND_RECOVERED = "ROLLED_BACK_AND_RECOVERED"
    ROLLED_BACK_BUT_INCIDENT_PERSISTS = "ROLLED_BACK_BUT_INCIDENT_PERSISTS"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    VERIFICATION_INCONCLUSIVE = "VERIFICATION_INCONCLUSIVE"

class LessonType(str):
    ROOT_CAUSE = "ROOT_CAUSE"
    REMEDIATION_EFFECTIVE = "REMEDIATION_EFFECTIVE"
    REMEDIATION_INEFFECTIVE = "REMEDIATION_INEFFECTIVE"
    ROLLBACK_EFFECTIVE = "ROLLBACK_EFFECTIVE"
    ROLLBACK_INEFFECTIVE = "ROLLBACK_INEFFECTIVE"
    PRECONDITION = "PRECONDITION"
    FAILURE_MODE = "FAILURE_MODE"
    VERIFICATION_PATTERN = "VERIFICATION_PATTERN"
    INFRASTRUCTURE_DRIFT = "INFRASTRUCTURE_DRIFT"
    CAPACITY_PATTERN = "CAPACITY_PATTERN"
    SECURITY_PATTERN = "SECURITY_PATTERN"
    CONFIGURATION_PATTERN = "CONFIGURATION_PATTERN"
    DEPENDENCY_PATTERN = "DEPENDENCY_PATTERN"
    NEGATIVE_KNOWLEDGE = "NEGATIVE_KNOWLEDGE"

class ConsolidationAction(str):
    CREATED = "CREATED"
    REINFORCED = "REINFORCED"
    MERGED = "MERGED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"

class RemediationOutcomeResponse(BaseModel):
    outcome_id: str
    incident_id: str
    plan_id: str
    execution_id: str
    execution_status: str
    verification_status: str
    incident_recovery_status: str
    outcome_classification: str
    effectiveness_score: float
    duration_seconds: float
    executed_steps_count: int
    failed_steps_count: int
    compensated_steps_count: int
    rollback_performed: bool
    rollback_successful: bool
    recovery_metrics: Dict[str, Any] = Field(default_factory=dict)
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: float
    created_at: str

class LearnedLessonResponse(BaseModel):
    lesson_id: str
    incident_id: str
    execution_id: Optional[str] = None
    lesson_type: str
    title: str
    statement: str
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    applicability_conditions: List[str] = Field(default_factory=list)
    non_applicability_conditions: List[str] = Field(default_factory=list)
    observed_effect: str
    confidence: float
    temporal_scope: str
    status: str

class MemoryCandidateResponse(BaseModel):
    candidate_id: str
    lesson_id: str
    candidate_text: str
    normalized_fingerprint: str
    source_incident_ids: List[str] = Field(default_factory=list)
    source_execution_ids: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: float
    novelty_score: float
    contradiction_score: float
    applicability_score: float
    quality_score: float
    review_required: bool
    rejection_reason: Optional[str] = None
    status: str

class ConsolidationRecordResponse(BaseModel):
    consolidation_id: str
    candidate_id: str
    target_memory_id: Optional[str] = None
    action: str
    reason: str
    previous_memory_ids: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    confidence_before: float
    confidence_after: float
    actor: str
    created_at: str

class MemoryFeedbackResponse(BaseModel):
    feedback_id: str
    memory_id: str
    incident_id: str
    retrieval_run_id: Optional[str] = None
    applicability: float
    used_for_investigation: bool
    used_for_remediation: bool
    remediation_result: str
    verification_result: str
    evidence_refs: List[str] = Field(default_factory=list)
    confidence_delta: float
    created_at: str

class ProvenanceChainResponse(BaseModel):
    memory_id: str
    title: str
    status: str
    confidence: float
    quality_score: float
    source_incident_id: Optional[str] = None
    source_execution_id: Optional[str] = None
    evidence_references: List[str] = Field(default_factory=list)
    valid_from: str
    valid_to: Optional[str] = None
    superseded_by: Optional[str] = None
    consolidation_history: List[ConsolidationRecordResponse] = Field(default_factory=list)
    feedback_history: List[MemoryFeedbackResponse] = Field(default_factory=list)

class ReviewQueueResponse(BaseModel):
    total_count: int
    candidates: List[MemoryCandidateResponse] = Field(default_factory=list)

class LearningSummaryResponse(BaseModel):
    incident_id: str
    outcome: RemediationOutcomeResponse
    lessons: List[LearnedLessonResponse] = Field(default_factory=list)
    candidates: List[MemoryCandidateResponse] = Field(default_factory=list)
    consolidations: List[ConsolidationRecordResponse] = Field(default_factory=list)
