from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from ghostops_shared import EntityType, TrustLevel

class MemoryVectorCreate(BaseModel):
    title: str
    content: str
    entity_type: Optional[EntityType] = None
    entity_id: Optional[str] = None
    incident_id: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    trust_level: TrustLevel = TrustLevel.MEDIUM

class MemorySearchQuery(BaseModel):
    query_text: str
    entity_type: Optional[EntityType] = None
    top_k: int = 5

class MemorySearchResult(BaseModel):
    id: str
    title: str
    content: str
    entity_type: Optional[EntityType]
    similarity_score: float
    trust_level: TrustLevel
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
