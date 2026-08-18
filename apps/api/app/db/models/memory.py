from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import String, Text, JSON, Float, ARRAY, Enum as SQLEnum, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ghostops_shared import EntityType, TrustLevel
from app.db.models.base import Base, TimestampMixin, UUIDMixin
from app.db.types import VectorType

class InstitutionalMemoryVector(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "institutional_memory_vectors"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    redacted_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    memory_type: Mapped[str] = mapped_column(String(50), default="symptom", nullable=False, index=True)

    # Entity & Incident references
    entity_type: Mapped[Optional[EntityType]] = mapped_column(SQLEnum(EntityType), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    incident_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    source_execution_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    evidence_references: Mapped[dict] = mapped_column(JSON, nullable=False, default=[])

    # Vector Embedding (CockroachDB Native VECTOR(1536) with SQLite JSON fallback)
    embedding: Mapped[list[float]] = mapped_column(VectorType(1536), nullable=False)

    # Metadata, Trust & Stage 7 Lifecycle / Provenance
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    trust_level: Mapped[TrustLevel] = mapped_column(
        SQLEnum(TrustLevel), default=TrustLevel.MEDIUM, nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    memory_status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False, index=True)  # ACTIVE | SUPERSEDED | ARCHIVED | REJECTED

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    applicability_conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    non_applicability_conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=[])

    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class RemediationOutcome(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "remediation_outcomes"

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("remediation_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_id: Mapped[str] = mapped_column(
        ForeignKey("remediation_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    execution_status: Mapped[str] = mapped_column(String(50), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False)
    incident_recovery_status: Mapped[str] = mapped_column(String(50), nullable=False)
    outcome_classification: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    effectiveness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    executed_steps_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_steps_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compensated_steps_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    rollback_performed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rollback_successful: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    before_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    after_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    recovery_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    evidence_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)

class LearnedLesson(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "learned_lessons"

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    lesson_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)

    supporting_evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    contradicting_evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    applicability_conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    non_applicability_conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=[])

    observed_effect: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    temporal_scope: Mapped[str] = mapped_column(String(255), default="v4.2.0+", nullable=False)
    source_memory_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    status: Mapped[str] = mapped_column(String(50), default="EXTRACTED", nullable=False)

class MemoryCandidate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "memory_candidates"

    lesson_id: Mapped[str] = mapped_column(
        ForeignKey("learned_lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_fingerprint: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Vector Embedding (CockroachDB Native VECTOR(1536) with SQLite JSON fallback)
    embedding: Mapped[list[float]] = mapped_column(VectorType(1536), nullable=False)
    source_incident_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    source_execution_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    evidence_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])

    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    novelty_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    contradiction_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    applicability_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)

    review_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING_REVIEW", nullable=False, index=True)

class MemoryConsolidationRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "memory_consolidations"

    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("memory_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_memory_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # CREATED | REINFORCED | MERGED | SUPERSEDED | REJECTED | FLAGGED_FOR_REVIEW
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    previous_memory_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    evidence_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    confidence_before: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_after: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actor: Mapped[str] = mapped_column(String(100), default="GhostOps.LearningConsolidator", nullable=False)

class MemoryFeedback(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "memory_feedback"

    memory_id: Mapped[str] = mapped_column(
        ForeignKey("institutional_memory_vectors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    retrieval_run_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    applicability: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    used_for_investigation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    used_for_remediation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    remediation_result: Mapped[str] = mapped_column(String(50), nullable=False)
    verification_result: Mapped[str] = mapped_column(String(50), nullable=False)

    evidence_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    confidence_delta: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
