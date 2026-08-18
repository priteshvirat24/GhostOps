from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from ghostops_shared import IncidentSeverity

class NormalizedOperationalEvent(BaseModel):
    event_id: str
    source: str  # e.g., 'cloudwatch', 'cloudtrail', 'aws_config'
    event_type: str  # e.g., 'ALARM_TRIGGERED', 'API_CALL', 'RESOURCE_CONFIG_CHANGE'
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service: str = "unknown-service"
    region: str = "us-east-1"
    resource_id: str = "unknown-resource"
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    message: str = ""
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestionRequestPayload(BaseModel):
    events: List[Dict[str, Any]]
    target_service: Optional[str] = None
    region: Optional[str] = "us-east-1"

class IngestionResultResponse(BaseModel):
    incident_id: str
    status: str  # COMPLETED, MEMORY_DEGRADED, EMBEDDING_PENDING
    events_received: int
    events_created: int
    duplicate_events: int
    memory_records_created: int
    embedding_records_created: int
    execution_time_ms: int
