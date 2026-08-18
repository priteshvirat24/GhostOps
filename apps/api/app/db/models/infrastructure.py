from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Boolean, Enum as SQLEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ghostops_shared import EntityType
from app.db.models.base import Base, TimestampMixin, UUIDMixin

class InfrastructureNode(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "infrastructure_nodes"

    resource_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    resource_type: Mapped[EntityType] = mapped_column(SQLEnum(EntityType), nullable=False)
    arn: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    aws_region: Mapped[str] = mapped_column(String(50), default="us-east-1", nullable=False)

    state_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    tags: Mapped[dict] = mapped_column(JSON, nullable=False, default={})

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

class InfrastructureSnapshot(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "infrastructure_snapshots"

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    db_version: Mapped[str] = mapped_column(String(100), default="CockroachDB v23.2.3", nullable=False)
    service_version: Mapped[str] = mapped_column(String(100), default="v1.0.0", nullable=False)
    topology: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    dependencies: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    resource_identifiers: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    region: Mapped[str] = mapped_column(String(50), default="us-east-1", nullable=False)
    traffic_info: Mapped[dict] = mapped_column(JSON, nullable=False, default={})

    incident: Mapped["Incident"] = relationship("Incident", back_populates="snapshots")
