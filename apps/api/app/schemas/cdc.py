from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum

class CDCOperation(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    RESOLVED = "RESOLVED"

class CDCProcessingStatus(str, Enum):
    PROCESSED = "PROCESSED"
    DUPLICATE_SKIPPED = "DUPLICATE_SKIPPED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"

class CDCEvent(BaseModel):
    event_id: str
    source_table: str
    primary_key: str
    operation: CDCOperation = CDCOperation.INSERT
    payload: Dict[str, Any] = Field(default_factory=dict)
    commit_timestamp: Optional[str] = None
    consumer_version: str = "v3.0.0"
    mode: str = "REAL_CDC"  # REAL_CDC | TEST_EVENT_MODE

class CDCProcessingResult(BaseModel):
    event_id: str
    status: CDCProcessingStatus
    source_table: str
    primary_key: str
    propagated_trust_delta: float = 0.0
    lessons_extracted_count: int = 0
    candidates_consolidated_count: int = 0
    reason: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CDCConsumerStatus(BaseModel):
    is_connected: bool
    mode: str  # REAL_CDC | TEST_EVENT_MODE
    events_received: int
    events_processed: int
    events_rejected: int
    duplicates_skipped: int
    last_processed_timestamp: Optional[str] = None
    last_event_id: Optional[str] = None
    source_tables: List[str] = Field(default_factory=list)
