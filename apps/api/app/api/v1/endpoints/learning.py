from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import (
    Incident,
    RemediationExecution,
    RemediationOutcome,
    LearnedLesson,
    MemoryCandidate,
    MemoryConsolidationRecord,
    InstitutionalMemoryVector,
    MemoryFeedback
)
from app.schemas.learning_memory import (
    LearningSummaryResponse,
    RemediationOutcomeResponse,
    LearnedLessonResponse,
    MemoryCandidateResponse,
    ConsolidationRecordResponse,
    MemoryFeedbackResponse,
    ProvenanceChainResponse,
    ReviewQueueResponse
)
from app.services.learning import (
    RemediationOutcomeAnalyzer,
    EffectivenessEvaluator,
    LessonExtractionService,
    MemoryCandidateGenerator,
    MemoryConsolidationService
)
from app.core.logging import logger

router = APIRouter()

def build_outcome_response(outc: RemediationOutcome) -> RemediationOutcomeResponse:
    return RemediationOutcomeResponse(
        outcome_id=outc.id,
        incident_id=outc.incident_id,
        plan_id=outc.plan_id,
        execution_id=outc.execution_id,
        execution_status=outc.execution_status,
        verification_status=outc.verification_status,
        incident_recovery_status=outc.incident_recovery_status,
        outcome_classification=outc.outcome_classification,
        effectiveness_score=outc.effectiveness_score,
        duration_seconds=outc.duration_seconds,
        executed_steps_count=outc.executed_steps_count,
        failed_steps_count=outc.failed_steps_count,
        compensated_steps_count=outc.compensated_steps_count,
        rollback_performed=outc.rollback_performed,
        rollback_successful=outc.rollback_successful,
        recovery_metrics=outc.recovery_metrics or {},
        evidence_refs=outc.evidence_refs or [],
        confidence=outc.confidence,
        created_at=outc.created_at.isoformat() if outc.created_at else ""
    )

def build_lesson_response(lesn: LearnedLesson) -> LearnedLessonResponse:
    return LearnedLessonResponse(
        lesson_id=lesn.id,
        incident_id=lesn.incident_id,
        execution_id=lesn.execution_id,
        lesson_type=lesn.lesson_type,
        title=lesn.title,
        statement=lesn.statement,
        supporting_evidence=lesn.supporting_evidence or [],
        contradicting_evidence=lesn.contradicting_evidence or [],
        applicability_conditions=lesn.applicability_conditions or [],
        non_applicability_conditions=lesn.non_applicability_conditions or [],
        observed_effect=lesn.observed_effect,
        confidence=lesn.confidence,
        temporal_scope=lesn.temporal_scope,
        status=lesn.status
    )

def build_candidate_response(cand: MemoryCandidate) -> MemoryCandidateResponse:
    return MemoryCandidateResponse(
        candidate_id=cand.id,
        lesson_id=cand.lesson_id,
        candidate_text=cand.candidate_text,
        normalized_fingerprint=cand.normalized_fingerprint,
        source_incident_ids=cand.source_incident_ids or [],
        source_execution_ids=cand.source_execution_ids or [],
        evidence_refs=cand.evidence_refs or [],
        confidence=cand.confidence,
        novelty_score=cand.novelty_score,
        contradiction_score=cand.contradiction_score,
        applicability_score=cand.applicability_score,
        quality_score=cand.quality_score,
        review_required=cand.review_required,
        rejection_reason=cand.rejection_reason,
        status=cand.status
    )

def build_consolidation_response(cons: MemoryConsolidationRecord) -> ConsolidationRecordResponse:
    return ConsolidationRecordResponse(
        consolidation_id=cons.id,
        candidate_id=cons.candidate_id,
        target_memory_id=cons.target_memory_id,
        action=cons.action,
        reason=cons.reason,
        previous_memory_ids=cons.previous_memory_ids or [],
        evidence_refs=cons.evidence_refs or [],
        confidence_before=cons.confidence_before,
        confidence_after=cons.confidence_after,
        actor=cons.actor,
        created_at=cons.created_at.isoformat() if cons.created_at else ""
    )

@router.post("/incidents/{incident_id}/learn", response_model=LearningSummaryResponse)
def trigger_post_remediation_learning(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Triggers post-remediation learning, lesson extraction, and institutional memory consolidation.
    Operation is strictly IDEMPOTENT.
    """
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

    execution = db.query(RemediationExecution).filter(
        RemediationExecution.incident_id == incident_id
    ).order_by(RemediationExecution.started_at.desc()).first()

    if not execution:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No execution record found for incident '{incident_id}'. Cannot extract learning without execution outcome.")

    # 1. Analyze Outcome
    outcome = RemediationOutcomeAnalyzer.analyze_execution_outcome(db, execution)

    # 2. Evaluate Effectiveness Score
    eff_score = EffectivenessEvaluator.evaluate_effectiveness(outcome)
    outcome.effectiveness_score = eff_score
    db.commit()

    # 3. Extract Lessons (Positive & Negative Knowledge)
    lessons = LessonExtractionService.extract_lessons(db, incident, execution, outcome)

    # 4. Generate Memory Candidates
    candidates = MemoryCandidateGenerator.generate_candidates(db, lessons)

    # 5. Consolidate Memory Lifecycle
    consolidations = MemoryConsolidationService.consolidate_candidates(db, candidates)

    return LearningSummaryResponse(
        incident_id=incident_id,
        outcome=build_outcome_response(outcome),
        lessons=[build_lesson_response(l) for l in lessons],
        candidates=[build_candidate_response(c) for c in candidates],
        consolidations=[build_consolidation_response(r) for r in consolidations]
    )

@router.get("/incidents/{incident_id}/learning", response_model=LearningSummaryResponse)
def get_incident_learning_summary(
    incident_id: str,
    db: Session = Depends(get_db)
):
    outcome = db.query(RemediationOutcome).filter(RemediationOutcome.incident_id == incident_id).first()
    if not outcome:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No learning summary exists for incident '{incident_id}'. Run POST /incidents/{incident_id}/learn first.")

    lessons = db.query(LearnedLesson).filter(LearnedLesson.incident_id == incident_id).all()

    cand_ids = [l.id for l in lessons]
    candidates = db.query(MemoryCandidate).filter(MemoryCandidate.lesson_id.in_(cand_ids)).all() if cand_ids else []

    c_ids = [c.id for c in candidates]
    consolidations = db.query(MemoryConsolidationRecord).filter(MemoryConsolidationRecord.candidate_id.in_(c_ids)).all() if c_ids else []

    return LearningSummaryResponse(
        incident_id=incident_id,
        outcome=build_outcome_response(outcome),
        lessons=[build_lesson_response(l) for l in lessons],
        candidates=[build_candidate_response(c) for c in candidates],
        consolidations=[build_consolidation_response(r) for r in consolidations]
    )

@router.get("/learning/review-queue", response_model=ReviewQueueResponse)
def list_review_queue(
    db: Session = Depends(get_db)
):
    cands = db.query(MemoryCandidate).filter(
        MemoryCandidate.review_required == True,
        MemoryCandidate.status == "FLAGGED_FOR_REVIEW"
    ).all()

    return ReviewQueueResponse(
        total_count=len(cands),
        candidates=[build_candidate_response(c) for c in cands]
    )

@router.post("/learning/candidates/{candidate_id}/approve", response_model=MemoryCandidateResponse)
def approve_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    cand = db.get(MemoryCandidate, candidate_id)
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate '{candidate_id}' not found.")

    cand.status = "APPROVED"
    cand.review_required = False
    db.commit()

    # Consolidate candidate into active memory
    MemoryConsolidationService.consolidate_candidates(db, [cand])
    return build_candidate_response(cand)

@router.post("/learning/candidates/{candidate_id}/reject", response_model=MemoryCandidateResponse)
def reject_candidate(
    candidate_id: str,
    rejection_reason: str = "Rejected during human review.",
    db: Session = Depends(get_db)
):
    cand = db.get(MemoryCandidate, candidate_id)
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate '{candidate_id}' not found.")

    cand.status = "REJECTED"
    cand.review_required = False
    cand.rejection_reason = rejection_reason
    db.commit()

    return build_candidate_response(cand)

@router.get("/memory/{memory_id}/provenance", response_model=ProvenanceChainResponse)
def get_memory_provenance(
    memory_id: str,
    db: Session = Depends(get_db)
):
    mem = db.get(InstitutionalMemoryVector, memory_id)
    if not mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory '{memory_id}' not found.")

    consolidations = db.query(MemoryConsolidationRecord).filter(
        MemoryConsolidationRecord.target_memory_id == memory_id
    ).all()

    feedbacks = db.query(MemoryFeedback).filter(
        MemoryFeedback.memory_id == memory_id
    ).all()

    fb_responses = [
        MemoryFeedbackResponse(
            feedback_id=f.id,
            memory_id=f.memory_id,
            incident_id=f.incident_id,
            retrieval_run_id=f.retrieval_run_id,
            applicability=f.applicability,
            used_for_investigation=f.used_for_investigation,
            used_for_remediation=f.used_for_remediation,
            remediation_result=f.remediation_result,
            verification_result=f.verification_result,
            evidence_refs=f.evidence_refs or [],
            confidence_delta=f.confidence_delta,
            created_at=f.created_at.isoformat() if f.created_at else ""
        ) for f in feedbacks
    ]

    return ProvenanceChainResponse(
        memory_id=mem.id,
        title=mem.title,
        status=mem.memory_status,
        confidence=mem.confidence,
        quality_score=0.90,
        source_incident_id=mem.incident_id,
        source_execution_id=mem.source_execution_id,
        evidence_references=mem.evidence_references or [],
        valid_from=mem.valid_from.isoformat() if mem.valid_from else "",
        valid_to=mem.valid_to.isoformat() if mem.valid_to else None,
        superseded_by=mem.superseded_by,
        consolidation_history=[build_consolidation_response(c) for c in consolidations],
        feedback_history=fb_responses
    )

@router.get("/memory/{memory_id}/feedback", response_model=List[MemoryFeedbackResponse])
def get_memory_feedback(
    memory_id: str,
    db: Session = Depends(get_db)
):
    feedbacks = db.query(MemoryFeedback).filter(MemoryFeedback.memory_id == memory_id).all()
    return [
        MemoryFeedbackResponse(
            feedback_id=f.id,
            memory_id=f.memory_id,
            incident_id=f.incident_id,
            retrieval_run_id=f.retrieval_run_id,
            applicability=f.applicability,
            used_for_investigation=f.used_for_investigation,
            used_for_remediation=f.used_for_remediation,
            remediation_result=f.remediation_result,
            verification_result=f.verification_result,
            evidence_refs=f.evidence_refs or [],
            confidence_delta=f.confidence_delta,
            created_at=f.created_at.isoformat() if f.created_at else ""
        ) for f in feedbacks
    ]
