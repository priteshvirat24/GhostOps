from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import String, Text, JSON, Float, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base import Base, TimestampMixin, UUIDMixin

class EvaluationRun(Base, UUIDMixin, TimestampMixin):
    """
    Persistent Evaluation Run for Counterfactual Replay & Benchmark Regressions (§9.5, §19.3).
    Stores versioned dataset metrics, safety floors, and aggregate evaluation results.
    """
    __tablename__ = "evaluation_runs"

    dataset_version: Mapped[str] = mapped_column(String(100), default="ghostops-golden-v1", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False, index=True) # RUNNING | COMPLETED | FAILED
    total_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    precision_at_1: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    precision_at_3: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mrr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    temporal_verdict_accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_grounding_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unsafe_replay_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    false_execution_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    regression_gate_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gate_details: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    cases: Mapped[List["EvaluationCaseResult"]] = relationship(
        "EvaluationCaseResult", back_populates="evaluation_run", cascade="all, delete-orphan"
    )

class EvaluationCaseResult(Base, UUIDMixin, TimestampMixin):
    """
    Individual case result in an evaluation run.
    """
    __tablename__ = "evaluation_case_results"

    evaluation_run_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    benchmark_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    incident_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    case_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    expected_root_cause: Mapped[str] = mapped_column(String(255), nullable=False)
    actual_hypothesis: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_precedent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    retrieved_precedent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    retrieval_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retrieval_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    expected_temporal_verdict: Mapped[str] = mapped_column(String(100), nullable=False)
    actual_temporal_verdict: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_safety_outcome: Mapped[str] = mapped_column(String(100), nullable=False)
    actual_safety_outcome: Mapped[str] = mapped_column(String(100), nullable=False)

    decision_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    safety_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    would_execute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    unsafe_execution: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evidence_grounding_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    trace_details: Mapped[dict] = mapped_column(JSON, nullable=False, default={})

    evaluation_run: Mapped["EvaluationRun"] = relationship("EvaluationRun", back_populates="cases")
