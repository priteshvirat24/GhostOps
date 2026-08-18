from pydantic import BaseModel
from typing import Dict, Any

class HealthResponse(BaseModel):
    status: str
    environment: str
    database_connected: bool
    aws_mock_mode: bool
    system_time: str
    details: Dict[str, Any]
