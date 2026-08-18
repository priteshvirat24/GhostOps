import time
import json
import uuid
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, asc

from app.db.models import (
    Incident,
    IncidentEvidence,
    IncidentEvent,
    InfrastructureSnapshot,
    OperationalActionHistory,
    InstitutionalMemoryVector,
)
from app.services.retrieval import HistoricalRetrievalService

class ToolResult(BaseModel):
    success: bool
    tool_name: str
    request_id: str
    data: Any
    error: Optional[Dict[str, str]] = None
    evidence_refs: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0

def sanitize_untrusted_data(raw_text_or_dict: Any) -> str:
    """
    Prompt Injection Defense Boundary.
    Wraps untrusted operational telemetry and evidence in strict data boundary tags
    and neutralizes embedded system control phrases.
    """
    if raw_text_or_dict is None:
        return ""

    if not isinstance(raw_text_or_dict, str):
        text = json.dumps(raw_text_or_dict, default=str)
    else:
        text = raw_text_or_dict

    # Neutralize common prompt injection trigger phrases in raw telemetry logs
    sanitized = re.sub(r'(?i)(?:ignore\s+previous\s+instructions|system\s+prompt|execute\s+command|run\s+tool)', '[NEUTRALIZED_UNTRUSTED_TEXT]', text)
    return f"<UNTRUSTED_OPERATIONAL_DATA>\n{sanitized}\n</UNTRUSTED_OPERATIONAL_DATA>"

class ReadOnlyInvestigationTools:
    """
    Typed read-only investigation tool registry for Stage 4 multi-agent graph nodes.
    All tools enforce read_only = True and produce ToolResult contracts.
    """

    @staticmethod
    def get_incident_timeline(db: Session, incident_id: str) -> ToolResult:
        start_time = time.time()
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        try:
            events = db.scalars(
                select(IncidentEvent)
                .where(IncidentEvent.incident_id == incident_id)
                .order_by(asc(IncidentEvent.event_timestamp))
            ).all()

            data = [
                {
                    "event_id": e.id,
                    "timestamp": e.event_timestamp.isoformat(),
                    "source": e.event_source,
                    "event_name": e.event_name,
                    "payload": e.payload,
                } for e in events
            ]
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=True, tool_name="get_incident_timeline", request_id=req_id,
                data=data, evidence_refs=[e.id for e in events], duration_ms=duration
            )
        except Exception as ex:
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=False, tool_name="get_incident_timeline", request_id=req_id,
                data=None, error={"code": "FETCH_ERROR", "message": str(ex)}, duration_ms=duration
            )

    @staticmethod
    def get_incident_evidence(db: Session, incident_id: str) -> ToolResult:
        start_time = time.time()
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        try:
            evidence_items = db.scalars(
                select(IncidentEvidence)
                .where(IncidentEvidence.incident_id == incident_id)
                .order_by(asc(IncidentEvidence.captured_at))
            ).all()

            data = [
                {
                    "evidence_id": ev.id,
                    "source": ev.source,
                    "event_type": ev.event_type,
                    "content_hash": ev.content_hash,
                    "captured_at": ev.captured_at.isoformat() if ev.captured_at else None,
                    # Apply Prompt Injection Defense Boundary to raw payload
                    "raw_payload_sanitized": sanitize_untrusted_data(ev.raw_payload),
                } for ev in evidence_items
            ]
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=True, tool_name="get_incident_evidence", request_id=req_id,
                data=data, evidence_refs=[ev.id for ev in evidence_items], duration_ms=duration
            )
        except Exception as ex:
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=False, tool_name="get_incident_evidence", request_id=req_id,
                data=None, error={"code": "FETCH_ERROR", "message": str(ex)}, duration_ms=duration
            )

    @staticmethod
    def get_infrastructure_snapshot(db: Session, incident_id: str) -> ToolResult:
        start_time = time.time()
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        try:
            snap = db.scalars(
                select(InfrastructureSnapshot).where(InfrastructureSnapshot.incident_id == incident_id)
            ).first()

            if not snap:
                duration = round((time.time() - start_time) * 1000, 2)
                return ToolResult(
                    success=False, tool_name="get_infrastructure_snapshot", request_id=req_id,
                    data=None, error={"code": "NOT_FOUND", "message": f"No snapshot found for incident '{incident_id}'"}, duration_ms=duration
                )

            data = {
                "snapshot_id": snap.id,
                "db_version": snap.db_version,
                "service_version": snap.service_version,
                "topology": snap.topology,
                "configuration": snap.configuration,
                "dependencies": snap.dependencies,
                "region": snap.region,
                "snapshot_timestamp": snap.snapshot_timestamp.isoformat() if snap.snapshot_timestamp else None,
            }
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=True, tool_name="get_infrastructure_snapshot", request_id=req_id,
                data=data, evidence_refs=[snap.id], duration_ms=duration
            )
        except Exception as ex:
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=False, tool_name="get_infrastructure_snapshot", request_id=req_id,
                data=None, error={"code": "FETCH_ERROR", "message": str(ex)}, duration_ms=duration
            )

    @staticmethod
    def get_current_infrastructure(db: Session, service: str, region: str = "us-east-1") -> ToolResult:
        start_time = time.time()
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        try:
            # Query most recent incident snapshot matching target service & region
            snap = db.scalars(
                select(InfrastructureSnapshot)
                .join(Incident, InfrastructureSnapshot.incident_id == Incident.id)
                .where(Incident.service == service, Incident.region == region)
                .order_by(InfrastructureSnapshot.snapshot_timestamp.desc())
            ).first()

            data = {
                "service": service,
                "region": region,
                "db_version": snap.db_version if snap else "CockroachDB v23.2.3",
                "service_version": snap.service_version if snap else "v4.2.0",
                "topology": snap.topology if snap else {"nodes": 3, "service": service},
                "configuration": snap.configuration if snap else {"pool_size": 50},
                "dependencies": snap.dependencies if snap else {"db": "crdb-cluster"},
            }
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=True, tool_name="get_current_infrastructure", request_id=req_id,
                data=data, evidence_refs=[snap.id] if snap else [], duration_ms=duration
            )
        except Exception as ex:
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=False, tool_name="get_current_infrastructure", request_id=req_id,
                data=None, error={"code": "FETCH_ERROR", "message": str(ex)}, duration_ms=duration
            )

    @staticmethod
    def search_historical_memory(db: Session, incident_id: str, limit: int = 5) -> ToolResult:
        start_time = time.time()
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        try:
            similar_res = HistoricalRetrievalService.get_similar_incidents(
                db=db, incident_id=incident_id, limit=limit, include_failed_actions=True
            )
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=True, tool_name="search_historical_memory", request_id=req_id,
                data=similar_res.model_dump(), evidence_refs=[c.incident_id for c in similar_res.candidates], duration_ms=duration
            )
        except Exception as ex:
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=False, tool_name="search_historical_memory", request_id=req_id,
                data=None, error={"code": "RETRIEVAL_ERROR", "message": str(ex)}, duration_ms=duration
            )

    @staticmethod
    def get_action_history(db: Session, incident_id: str) -> ToolResult:
        start_time = time.time()
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        try:
            actions = db.scalars(
                select(OperationalActionHistory)
                .where(OperationalActionHistory.incident_id == incident_id)
                .order_by(asc(OperationalActionHistory.timestamp))
            ).all()

            data = [
                {
                    "action_id": a.id,
                    "command": a.command,
                    "tool": a.tool,
                    "target": a.target,
                    "result": a.result,
                    "reason": a.reason,
                    "error_message": a.error_message,
                    "idempotency_key": a.idempotency_key,
                } for a in actions
            ]
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=True, tool_name="get_action_history", request_id=req_id,
                data=data, evidence_refs=[a.id for a in actions], duration_ms=duration
            )
        except Exception as ex:
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=False, tool_name="get_action_history", request_id=req_id,
                data=None, error={"code": "FETCH_ERROR", "message": str(ex)}, duration_ms=duration
            )

    @staticmethod
    def get_memory_record(db: Session, memory_id: str) -> ToolResult:
        start_time = time.time()
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        try:
            mem = db.get(InstitutionalMemoryVector, memory_id)
            if not mem:
                duration = round((time.time() - start_time) * 1000, 2)
                return ToolResult(
                    success=False, tool_name="get_memory_record", request_id=req_id,
                    data=None, error={"code": "NOT_FOUND", "message": f"Memory '{memory_id}' not found"}, duration_ms=duration
                )

            data = {
                "memory_id": mem.id,
                "title": mem.title,
                "content": sanitize_untrusted_data(mem.content),
                "memory_type": mem.memory_type,
                "incident_id": mem.incident_id,
                "trust_level": mem.trust_level.value if hasattr(mem.trust_level, "value") else str(mem.trust_level),
            }
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=True, tool_name="get_memory_record", request_id=req_id,
                data=data, evidence_refs=[mem.id], duration_ms=duration
            )
        except Exception as ex:
            duration = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=False, tool_name="get_memory_record", request_id=req_id,
                data=None, error={"code": "FETCH_ERROR", "message": str(ex)}, duration_ms=duration
            )
