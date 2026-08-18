from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ghostops_shared import AgentStepStatus
from app.db.models.base import Base, TimestampMixin, UUIDMixin

class AgentTrace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_traces"

    incident_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True
    )
    graph_name: Mapped[str] = mapped_column(String(100), default="ghostops_orchestrator", nullable=False)
    thread_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    status: Mapped[AgentStepStatus] = mapped_column(
        SQLEnum(AgentStepStatus), default=AgentStepStatus.RUNNING, nullable=False
    )
    current_node: Mapped[str] = mapped_column(String(100), default="sentinel", nullable=False)
    
    # State snapshot & history
    state_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default={})

    step_executions: Mapped[List["AgentStepExecution"]] = relationship(
        "AgentStepExecution", back_populates="trace", cascade="all, delete-orphan"
    )

class AgentStepExecution(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_step_executions"

    trace_id: Mapped[str] = mapped_column(
        ForeignKey("agent_traces.id", ondelete="CASCADE"), nullable=False
    )
    node_name: Mapped[str] = mapped_column(String(100), nullable=False) # sentinel, historian, investigator, temporal_reasoning, validation, execution, verification
    status: Mapped[AgentStepStatus] = mapped_column(
        SQLEnum(AgentStepStatus), default=AgentStepStatus.PENDING, nullable=False
    )
    input_state: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    output_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tool_calls: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    execution_time_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    error_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    trace: Mapped["AgentTrace"] = relationship("AgentTrace", back_populates="step_executions")
