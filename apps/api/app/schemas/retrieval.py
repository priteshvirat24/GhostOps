from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class MatchedFields(BaseModel):
    service: bool = False
    region: bool = False
    symptom: bool = False
    resource_type: bool = False
    db_version: bool = False
    service_version: bool = False

class HistoricalMemoryCandidateResponse(BaseModel):
    incident_id: str
    rank: int
    title: str
    service: str
    region: str
    severity: str
    status: str
    start_time: str
    hybrid_score: float
    structured_score: float
    semantic_score: float
    outcome_score: float
    trust_score: float
    staleness_penalty: float
    matched_fields: Dict[str, bool]
    outcome_summary: str
    failed_actions: List[Dict[str, Any]] = Field(default_factory=list)
    successful_actions: List[Dict[str, Any]] = Field(default_factory=list)
    infrastructure_snapshot_summary: Dict[str, Any] = Field(default_factory=dict)
    memory_records: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)

class SimilarIncidentsResponse(BaseModel):
    target_incident_id: str
    candidates_count: int
    candidates: List[HistoricalMemoryCandidateResponse]

class MemorySearchRequestPayload(BaseModel):
    query_text: str
    service: Optional[str] = None
    region: Optional[str] = None
    severity: Optional[str] = None
    limit: int = 5
    memory_type: Optional[str] = None
