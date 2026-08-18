from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import String, Text, JSON, Float, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base import Base, TimestampMixin, UUIDMixin

class ReplayRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "replay_runs"

    source_incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_execution_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    source_snapshot_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    memory_version: Mapped[str] = mapped_column(String(100), default="v1.0", nullable=False)
    mode: Mapped[str] = mapped_column(String(100), default="HISTORICAL_REPLAY", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)

    deterministic_seed: Mapped[int] = mapped_column(Integer, default=42, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    predicted_outcome: Mapped[str] = mapped_column(String(100), default="UNKNOWN", nullable=False)
    actual_outcome: Mapped[str] = mapped_column(String(100), default="UNKNOWN", nullable=False)

    replay_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    termination_reason: Mapped[str] = mapped_column(String(100), default="COMPLETED_SUCCESSFULLY", nullable=False)

    scenarios: Mapped[List["ReplayScenarioRecord"]] = relationship(
        "ReplayScenarioRecord", back_populates="replay_run", cascade="all, delete-orphan"
    )
    steps: Mapped[List["ReplayStepRecord"]] = relationship(
        "ReplayStepRecord", back_populates="replay_run", cascade="all, delete-orphan", order_by="ReplayStepRecord.step_order"
    )
    differences: Mapped[List["ReplayDifferenceRecord"]] = relationship(
        "ReplayDifferenceRecord", back_populates="replay_run", cascade="all, delete-orphan"
    )
    regressions: Mapped[List["MemoryRegressionRecord"]] = relationship(
        "MemoryRegressionRecord", back_populates="replay_run", cascade="all, delete-orphan"
    )
    mutations: Mapped[List["SimulationMutationRecord"]] = relationship(
        "SimulationMutationRecord", back_populates="replay_run", cascade="all, delete-orphan"
    )

class ReplayScenarioRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "replay_scenarios"

    replay_id: Mapped[str] = mapped_column(
        ForeignKey("replay_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    completeness_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    infrastructure_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    incident_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    telemetry_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    memory_context: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    scenario_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    replay_run: Mapped["ReplayRun"] = relationship("ReplayRun", back_populates="scenarios")

class ReplayStepRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "replay_step_records"

    replay_id: Mapped[str] = mapped_column(
        ForeignKey("replay_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_resource: Mapped[str] = mapped_column(String(512), nullable=False)

    input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    output_summary: Mapped[str] = mapped_column(Text, nullable=False)

    simulated_pre_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    simulated_post_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    evidence_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])

    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUCCEEDED", nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    replay_run: Mapped["ReplayRun"] = relationship("ReplayRun", back_populates="steps")

class ReplayDifferenceRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "replay_differences"

    replay_id: Mapped[str] = mapped_column(
        ForeignKey("replay_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # DIAGNOSIS | REMEDIATION | OUTCOME | STATE
    historical_value: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    predicted_value: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    severity: Mapped[str] = mapped_column(String(50), default="LOW", nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])

    replay_run: Mapped["ReplayRun"] = relationship("ReplayRun", back_populates="differences")

class MemoryRegressionRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "memory_regressions"

    replay_id: Mapped[str] = mapped_column(
        ForeignKey("replay_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    memory_id: Mapped[str] = mapped_column(
        ForeignKey("institutional_memory_vectors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    regression_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    previous_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    observed_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    score_delta: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DETECTED", nullable=False)

    replay_run: Mapped["ReplayRun"] = relationship("ReplayRun", back_populates="regressions")

class SimulationMutationRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "simulation_mutations"

    replay_id: Mapped[str] = mapped_column(
        ForeignKey("replay_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    pre_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    post_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    simulated_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reversible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mutation_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    replay_run: Mapped["ReplayRun"] = relationship("ReplayRun", back_populates="mutations")
