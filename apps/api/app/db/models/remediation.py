from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum, Boolean, UniqueConstraint, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ghostops_shared import RemediationStatus
from app.db.models.base import Base, TimestampMixin, UUIDMixin

class RemediationPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "remediation_plans"

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    investigation_run_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RemediationStatus] = mapped_column(
        SQLEnum(RemediationStatus),
        default=RemediationStatus.PENDING_APPROVAL,
        nullable=False,
        index=True
    )

    root_cause_hypothesis_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    compatibility_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    compatibility_classification: Mapped[str] = mapped_column(String(100), default="UNKNOWN", nullable=False)

    estimated_risk: Mapped[str] = mapped_column(String(50), default="LOW", nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    blast_radius: Mapped[str] = mapped_column(String(50), default="LOCAL", nullable=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    approval_gate: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    safety_checks: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    rollback_plan: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    verification_plan: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    evidence_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    historical_precedent_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])

    steps: Mapped[List["PlanStep"]] = relationship(
        "PlanStep", back_populates="remediation_plan", cascade="all, delete-orphan", order_by="PlanStep.step_order"
    )

class PlanStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "plan_steps"

    remediation_plan_id: Mapped[str] = mapped_column(
        ForeignKey("remediation_plans.id", ondelete="CASCADE"), nullable=False
    )
    step_order: Mapped[int] = mapped_column(nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_resource_arn: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    rollback_parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default={})

    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    execution_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    remediation_plan: Mapped["RemediationPlan"] = relationship("RemediationPlan", back_populates="steps")

class RemediationExecution(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "remediation_executions"

    plan_id: Mapped[str] = mapped_column(
        ForeignKey("remediation_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    termination_reason: Mapped[str] = mapped_column(String(100), default="IN_PROGRESS", nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    executed_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compensated_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    verification_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    incident_recovery_status: Mapped[str] = mapped_column(String(50), default="UNKNOWN", nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(50), default="MOCK", nullable=False)

    lock_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    executor: Mapped[str] = mapped_column(String(100), default="GhostOps.SagaEngine", nullable=False)
    trace_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    steps_detail: Mapped[List["ExecutionStepRecord"]] = relationship(
        "ExecutionStepRecord", back_populates="execution", cascade="all, delete-orphan", order_by="ExecutionStepRecord.step_order"
    )
    events: Mapped[List["ExecutionEventRecord"]] = relationship(
        "ExecutionEventRecord", back_populates="execution", cascade="all, delete-orphan", order_by="ExecutionEventRecord.created_at"
    )

class ExecutionStepRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "execution_step_records"

    execution_id: Mapped[str] = mapped_column(
        ForeignKey("remediation_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_step_id: Mapped[str] = mapped_column(String(255), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_resource: Mapped[str] = mapped_column(String(512), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(50), default="MOCK", nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    pre_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    post_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})

    compensation_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)

    execution: Mapped["RemediationExecution"] = relationship("RemediationExecution", back_populates="steps_detail")

class ExecutionLockRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "execution_locks"

    resource_scope: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    plan_id: Mapped[str] = mapped_column(String(255), nullable=False)
    execution_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False, index=True)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class ExecutionEventRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "execution_events"

    execution_id: Mapped[str] = mapped_column(
        ForeignKey("remediation_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(100), default="GhostOps.SagaEngine", nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    severity: Mapped[str] = mapped_column(String(50), default="INFO", nullable=False)

    execution: Mapped["RemediationExecution"] = relationship("RemediationExecution", back_populates="events")

class OperationalActionHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "operational_actions"

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    saga_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actor: Mapped[str] = mapped_column(String(100), default="GhostOps.Orchestrator", nullable=False)
    agent: Mapped[str] = mapped_column(String(100), default="RemediationEngine", nullable=False)
    command: Mapped[str] = mapped_column(String(255), nullable=False)
    tool: Mapped[str] = mapped_column(String(100), nullable=False)
    target: Mapped[str] = mapped_column(String(512), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(50), default="MOCK", nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), default="LOW", nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    authorization: Mapped[str] = mapped_column("authorization", String(100), quote=True, default="SystemAutoApproved", nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    result: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    incident: Mapped["Incident"] = relationship("Incident", back_populates="actions")

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_action_idempotency_key"),
    )
