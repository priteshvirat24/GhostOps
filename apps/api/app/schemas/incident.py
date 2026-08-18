from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from ghostops_shared import IncidentSeverity, IncidentStatus

class IncidentEventBase(BaseModel):
    event_source: str
    event_name: str
    event_timestamp: datetime
    payload: Dict[str, Any] = {}

class IncidentEventCreate(IncidentEventBase):
    pass

class IncidentEventResponse(IncidentEventBase):
    id: str
    incident_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IncidentBase(BaseModel):
    title: str
    description: str
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    target_resource_id: Optional[str] = None

class IncidentCreate(IncidentBase):
    events: List[IncidentEventCreate] = []

class IncidentResponse(IncidentBase):
    id: str
    status: IncidentStatus
    root_cause_summary: Optional[str] = None
    resolution_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    events: List[IncidentEventResponse] = []

    model_config = ConfigDict(from_attributes=True)
