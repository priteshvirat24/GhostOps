from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ghostops_shared import IncidentSeverity, IncidentStatus, TrustLevel
from app.db.models.base import Base, TimestampMixin, UUIDMixin
from app.db.types import VectorType

class Incident(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incidents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(
        SQLEnum(IncidentSeverity),
        default=IncidentSeverity.MEDIUM,
        nullable=False,
        index=True
    )
    status: Mapped[IncidentStatus] = mapped_column(
        SQLEnum(IncidentStatus),
        default=IncidentStatus.OPEN,
        nullable=False,
        index=True
    )
    service: Mapped[str] = mapped_column(String(100), default="web-service", nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(50), default="us-east-1", nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    target_resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    environment_fingerprint: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    root_cause_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    memory_status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    # Vector Embedding (CockroachDB Native VECTOR(1536) with SQLite JSON fallback)
    summary_embedding: Mapped[Optional[list[float]]] = mapped_column(
        VectorType(1536), nullable=True
    )

    events: Mapped[List["IncidentEvent"]] = relationship(
        "IncidentEvent", back_populates="incident", cascade="all, delete-orphan"
    )
    evidence: Mapped[List["IncidentEvidence"]] = relationship(
        "IncidentEvidence", back_populates="incident", cascade="all, delete-orphan"
    )
    snapshots: Mapped[List["InfrastructureSnapshot"]] = relationship(
        "InfrastructureSnapshot", back_populates="incident", cascade="all, delete-orphan"
    )
    actions: Mapped[List["OperationalActionHistory"]] = relationship(
        "OperationalActionHistory", back_populates="incident", cascade="all, delete-orphan"
    )

class IncidentEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incident_events"

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    event_source: Mapped[str] = mapped_column(String(100), nullable=False)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default={})

    incident: Mapped["Incident"] = relationship("Incident", back_populates="events")

class IncidentEvidence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incident_evidence"

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. cloudwatch, cloudtrail, aws_config
    source_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trust_level: Mapped[TrustLevel] = mapped_column(
        SQLEnum(TrustLevel), default=TrustLevel.MEDIUM, nullable=False
    )

    incident: Mapped["Incident"] = relationship("Incident", back_populates="evidence")

    __table_args__ = (
        UniqueConstraint("source", "source_event_id", name="uq_evidence_source_event_id"),
    )
