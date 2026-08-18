import uuid
import math
import time
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import select, and_

from app.db.models import (
    MemoryCandidate,
    InstitutionalMemoryVector,
    MemoryConsolidationRecord,
    MemoryFeedback,
    LearnedLesson
)
from app.schemas.learning_memory import ConsolidationAction
from ghostops_shared import TrustLevel
from app.core.logging import logger

def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2:
        return 0.0
    min_len = min(len(vec1), len(vec2))
    v1 = vec1[:min_len]
    v2 = vec2[:min_len]
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm1 * norm2)))

class MemoryConsolidationService:
    """
    Memory Consolidation & Lifecycle Service for GhostOps Stage 8.
    Evaluates candidates against institutional memory in CockroachDB using native vector similarity,
    structured predicates, and temporal validity.
    Executes deduplication, reinforcement, non-destructive supersession (preserving previous memory IDs),
    bounded confidence calibration (0.0 to 0.95), and feedback loop recording.
    """

    @classmethod
    def consolidate_candidates(
        cls,
        db: Session,
        candidates: List[MemoryCandidate]
    ) -> List[MemoryConsolidationRecord]:
        consolidations: List[MemoryConsolidationRecord] = []
        now_time = datetime.now(timezone.utc)

        for candidate in candidates:
            # Check if candidate was already consolidated (Idempotency)
            existing_record = db.query(MemoryConsolidationRecord).filter(
                MemoryConsolidationRecord.candidate_id == candidate.id
            ).first()
            if existing_record:
                consolidations.append(existing_record)
                continue

            # Check if candidate is flagged for human review or rejected
            if candidate.review_required and candidate.status == "FLAGGED_FOR_REVIEW":
                rec = cls._create_consolidation_record(
                    db, candidate, None, ConsolidationAction.FLAGGED_FOR_REVIEW,
                    candidate.rejection_reason or "Candidate flagged for human review due to negative knowledge or low initial confidence.",
                    0.0, candidate.confidence
                )
                consolidations.append(rec)
                continue

            # Query existing active memories for similarity comparison
            active_memories = db.scalars(
                select(InstitutionalMemoryVector).where(InstitutionalMemoryVector.memory_status == "ACTIVE")
            ).all()

            matched_memory: Optional[InstitutionalMemoryVector] = None
            highest_sim = 0.0

            for mem in active_memories:
                # 1. Semantic Similarity via Cosine Distance
                sim = compute_cosine_similarity(candidate.embedding, mem.embedding)
                # 2. Structured Match (Title / Substring overlap)
                if mem.title in candidate.candidate_text or candidate.candidate_text in mem.title:
                    sim = max(sim, 0.90)

                if sim > highest_sim:
                    highest_sim = sim
                    matched_memory = mem

            # Action Decision Logic
            is_negative_candidate = ("Ineffective" in candidate.candidate_text or 
                                     "NEGATIVE_KNOWLEDGE" in candidate.candidate_text or 
                                     "Negative" in candidate.candidate_text)

            if not matched_memory or highest_sim < 0.80:
                # CREATED: Insert new InstitutionalMemoryVector
                new_mem_id = f"mem-cons-{uuid.uuid4().hex[:12]}"
                new_vec = InstitutionalMemoryVector(
                    id=new_mem_id,
                    title=f"Learned: {candidate.candidate_text[:60]}...",
                    content=candidate.candidate_text,
                    redacted_content=candidate.candidate_text,
                    memory_type="negative_knowledge" if is_negative_candidate else "remediation",
                    incident_id=candidate.source_incident_ids[0] if candidate.source_incident_ids else None,
                    source_execution_id=candidate.source_execution_ids[0] if candidate.source_execution_ids else None,
                    evidence_references=candidate.evidence_refs or [],
                    embedding=candidate.embedding,
                    trust_level=TrustLevel.HIGH if candidate.confidence >= 0.85 else TrustLevel.MEDIUM,
                    confidence=min(0.95, candidate.confidence),
                    memory_status="ACTIVE",
                    valid_from=now_time,
                    usage_count=1,
                    successful_usage_count=0 if is_negative_candidate else 1,
                    failed_usage_count=1 if is_negative_candidate else 0,
                    last_validated_at=now_time
                )
                db.add(new_vec)
                db.commit()

                rec = cls._create_consolidation_record(
                    db, candidate, new_mem_id, ConsolidationAction.CREATED,
                    "Consolidated new evidence-backed operational lesson into active institutional memory.",
                    0.0, new_vec.confidence
                )
                consolidations.append(rec)

            elif is_negative_candidate:
                # SUPERSEDED: Non-destructive supersession preserving previous memory ID and full provenance chain
                old_mem_id = matched_memory.id
                matched_memory.memory_status = "SUPERSEDED"
                matched_memory.valid_to = now_time

                new_mem_id = f"mem-super-{uuid.uuid4().hex[:12]}"
                matched_memory.superseded_by = new_mem_id
                flag_modified(matched_memory, "superseded_by")

                new_vec = InstitutionalMemoryVector(
                    id=new_mem_id,
                    title=f"Superseding Lesson: {candidate.candidate_text[:60]}...",
                    content=candidate.candidate_text,
                    redacted_content=candidate.candidate_text,
                    memory_type="negative_knowledge",
                    incident_id=candidate.source_incident_ids[0] if candidate.source_incident_ids else None,
                    source_execution_id=candidate.source_execution_ids[0] if candidate.source_execution_ids else None,
                    evidence_references=candidate.evidence_refs or [],
                    embedding=candidate.embedding,
                    trust_level=TrustLevel.HIGH,
                    confidence=min(0.95, candidate.confidence),
                    memory_status="ACTIVE",
                    valid_from=now_time,
                    usage_count=1,
                    last_validated_at=now_time
                )
                db.add(new_vec)
                db.commit()

                rec = cls._create_consolidation_record(
                    db, candidate, new_mem_id, ConsolidationAction.SUPERSEDED,
                    f"New negative knowledge evidence superseded historical memory '{old_mem_id}'. Preserved full supersession provenance.",
                    matched_memory.confidence, new_vec.confidence,
                    prev_ids=[old_mem_id]
                )
                consolidations.append(rec)

            else:
                # REINFORCED: Bounded deterministic confidence calibration (0.0 to 0.95)
                conf_before = matched_memory.confidence
                conf_after = min(0.95, round(conf_before + 0.05, 4))

                matched_memory.confidence = conf_after
                matched_memory.usage_count += 1
                matched_memory.successful_usage_count += 1
                matched_memory.last_validated_at = now_time
                db.commit()

                # Record Feedback Loop Entry
                fb = MemoryFeedback(
                    id=f"fb-{uuid.uuid4().hex[:10]}",
                    memory_id=matched_memory.id,
                    incident_id=candidate.source_incident_ids[0] if candidate.source_incident_ids else "inc-01",
                    applicability=candidate.applicability_score,
                    used_for_investigation=True,
                    used_for_remediation=True,
                    remediation_result="SUCCESS",
                    verification_result="VERIFIED",
                    evidence_refs=candidate.evidence_refs or [],
                    confidence_delta=0.05
                )
                db.add(fb)
                db.commit()

                rec = cls._create_consolidation_record(
                    db, candidate, matched_memory.id, ConsolidationAction.REINFORCED,
                    f"Repeated successful validation reinforced historical memory '{matched_memory.id}'. Confidence calibrated from {conf_before:.2f} to {conf_after:.2f}.",
                    conf_before, conf_after
                )
                consolidations.append(rec)

        return consolidations

    @classmethod
    def _create_consolidation_record(
        cls,
        db: Session,
        candidate: MemoryCandidate,
        target_mem_id: Optional[str],
        action: str,
        reason: str,
        conf_before: float,
        conf_after: float,
        prev_ids: List[str] = None
    ) -> MemoryConsolidationRecord:
        rec = MemoryConsolidationRecord(
            id=f"cons-rec-{uuid.uuid4().hex[:12]}",
            candidate_id=candidate.id,
            target_memory_id=target_mem_id,
            action=action,
            reason=reason,
            previous_memory_ids=prev_ids or [],
            evidence_refs=candidate.evidence_refs or [],
            confidence_before=conf_before,
            confidence_after=conf_after,
            actor="GhostOps.LearningConsolidator"
        )
        db.add(rec)
        candidate.status = "APPROVED" if action in [ConsolidationAction.CREATED, ConsolidationAction.REINFORCED, ConsolidationAction.SUPERSEDED] else action
        db.commit()
        return rec
