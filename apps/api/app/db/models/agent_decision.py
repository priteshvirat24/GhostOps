from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Text, JSON, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base, TimestampMixin, UUIDMixin

class AgentDecision(Base, UUIDMixin, TimestampMixin):
    """
    Append-only Agent Decision Ledger for GhostOps Stage 4 & PRD v3.0 (§20, §26).
    Records agent reasoning, input summary, structured output, confidence,
    and explicit disagreement flags.
    """
    __tablename__ = "agent_decisions"

    incident_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    agent: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    disagreement_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
