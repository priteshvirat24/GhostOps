from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Text, JSON, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base, TimestampMixin, UUIDMixin

class CDCProcessedEvent(Base, UUIDMixin, TimestampMixin):
    """
    Durable Idempotency Ledger for CockroachDB Changefeed Events (§19.2).
    Tracks every processed changefeed event to prevent duplicate side effects on restarts or retries.
    """
    __tablename__ = "cdc_processed_events"

    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    source_table: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    primary_key: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False) # INSERT | UPDATE | DELETE
    status: Mapped[str] = mapped_column(String(50), default="PROCESSED", nullable=False) # PROCESSED | REJECTED | FAILED

    propagated_trust_delta: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    processing_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default={})
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

class CDCStreamCursor(Base, UUIDMixin, TimestampMixin):
    """
    Persistent cursor for CockroachDB changefeed stream recovery.
    """
    __tablename__ = "cdc_stream_cursors"

    feed_name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    last_resolved_timestamp: Mapped[str] = mapped_column(String(255), nullable=False)
    events_processed_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
