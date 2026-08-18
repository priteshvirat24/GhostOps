from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import String, Text, JSON, Float, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base import Base, TimestampMixin, UUIDMixin

class SentinelInstance(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sentinel_instances"

    sentinel_id: Mapped[str] = mapped_column(String(100), default="sentinel-primary", nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="GhostOps Primary Sentinel", nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="STOPPED", nullable=False, index=True)  # STARTING | RUNNING | DEGRADED | PAUSED | STOPPING | STOPPED | FAILED
    mode: Mapped[str] = mapped_column(String(100), default="DETECT_INVESTIGATE_AND_PLAN", nullable=False, index=True)  # OBSERVE_ONLY | DETECT_AND_INVESTIGATE | DETECT_INVESTIGATE_AND_PLAN
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_event_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    consecutive_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    events_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incidents_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    investigations_triggered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    plans_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

class SentinelEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sentinel_events"

    event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    sentinel_id: Mapped[str] = mapped_column(String(100), default="sentinel-primary", nullable=False, index=True)

    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # CloudWatch | CloudTrail | AWSConfig | MockIngestion
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), default="EC2", nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    severity: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False)

    metric_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    baseline_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    region: Mapped[str] = mapped_column(String(50), default="us-east-1", nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    correlation_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    deduplication_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    suppressed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suppression_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    incident_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )

class SentinelAlert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sentinel_alerts"

    alert_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    sentinel_id: Mapped[str] = mapped_column(String(100), default="sentinel-primary", nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False)

    anomaly_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False, index=True)  # OPEN | CORRELATED | SUPPRESSED | RESOLVED | ESCALATED

    deduplication_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    correlation_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    occurrence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    suppressed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    incident_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )

class SentinelIncidentLink(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sentinel_incident_links"

    alert_id: Mapped[str] = mapped_column(
        ForeignKey("sentinel_alerts.alert_id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship: Mapped[str] = mapped_column(String(100), default="PRIMARY_SIGNAL", nullable=False)  # PRIMARY_SIGNAL | RELATED_SIGNAL | DUPLICATE_SIGNAL | FOLLOWUP_SIGNAL
    confidence: Mapped[float] = mapped_column(Float, default=0.9, nullable=False)

class SentinelDecision(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sentinel_decisions"

    decision_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    sentinel_id: Mapped[str] = mapped_column(String(100), default="sentinel-primary", nullable=False, index=True)

    event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    decision_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # IGNORE | SUPPRESS | CREATE_INCIDENT | CORRELATE | TRIGGER_INVESTIGATION | TRIGGER_REPLAY | CREATE_PLAN | ESCALATE | PAUSE_SENTINEL
    decision: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)

    evidence_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    policy_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=[])

class SentinelRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sentinel_runs"

    run_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    sentinel_id: Mapped[str] = mapped_column(String(100), default="sentinel-primary", nullable=False, index=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    events_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    events_normalized: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    alerts_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    alerts_suppressed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incidents_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    investigations_triggered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    replays_triggered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    plans_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    errors: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    termination_reason: Mapped[str] = mapped_column(String(100), default="COMPLETED_CLEANLY", nullable=False)

class SentinelPolicy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sentinel_policies"

    policy_id: Mapped[str] = mapped_column(String(100), default="pol-default", nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="Default Sentinel Policy", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    severity_threshold: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False)
    anomaly_threshold: Mapped[float] = mapped_column(Float, default=0.65, nullable=False)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.70, nullable=False)

    dedup_window_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    correlation_window_seconds: Mapped[int] = mapped_column(Integer, default=600, nullable=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    max_incidents_per_window: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_investigations_per_window: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_replays_per_window: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    auto_plan_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
