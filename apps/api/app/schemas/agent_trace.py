from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from ghostops_shared import AgentStepStatus

class StepExecutionResponse(BaseModel):
    id: str
    node_name: str
    status: AgentStepStatus
    input_state: Dict[str, Any]
    output_state: Optional[Dict[str, Any]] = None
    tool_calls: Dict[str, Any] = {}
    execution_time_ms: Optional[int] = None
    error_log: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AgentTraceResponse(BaseModel):
    id: str
    incident_id: Optional[str] = None
    graph_name: str
    thread_id: str
    status: AgentStepStatus
    current_node: str
    state_snapshot: Dict[str, Any]
    step_executions: List[StepExecutionResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
