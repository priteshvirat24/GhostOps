from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, asc

from app.db.session import get_db
from app.db.models import (
    Incident,
    IncidentEvidence,
    IncidentEvent,
    InfrastructureSnapshot,
    OperationalActionHistory,
    InstitutionalMemoryVector,
)
from app.schemas.normalized_event import IngestionRequestPayload, IngestionResultResponse
from app.schemas.retrieval import SimilarIncidentsResponse
from app.services.ingestion_service import IncidentIngestionService
from app.services.retrieval.retrieval_service import HistoricalRetrievalService

router = APIRouter()

@router.post("/ingest", response_model=IngestionResultResponse, status_code=201)
def ingest_events(payload: IngestionRequestPayload, db: Session = Depends(get_db)):
    """POST /api/v1/incidents/ingest - Perform actual transactional ingestion of raw events."""
    try:
        return IncidentIngestionService.ingest_operational_events(
            db=db,
            raw_events=payload.events,
            target_service=payload.target_service,
            region=payload.region
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

@router.get("", response_model=List[Dict[str, Any]])
def list_incidents(
    severity: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """GET /api/v1/incidents - List incidents with optional filters."""
    stmt = select(Incident)
    if severity:
        stmt = stmt.where(Incident.severity == severity)
    if service:
        stmt = stmt.where(Incident.service == service)
    if region:
        stmt = stmt.where(Incident.region == region)
    if status:
        stmt = stmt.where(Incident.status == status)

    stmt = stmt.order_by(Incident.created_at.desc())
    incidents = db.scalars(stmt).all()

    return [
        {
            "id": inc.id,
            "title": inc.title,
            "description": inc.description,
            "severity": inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
            "status": inc.status.value if hasattr(inc.status, "value") else str(inc.status),
            "service": inc.service,
            "region": inc.region,
            "start_time": inc.start_time.isoformat(),
            "end_time": inc.end_time.isoformat() if inc.end_time else None,
            "target_resource_id": inc.target_resource_id,
            "memory_status": inc.memory_status,
            "created_at": inc.created_at.isoformat(),
        } for inc in incidents
    ]

@router.get("/{incident_id}", response_model=Dict[str, Any])
def get_incident_detail(incident_id: str, db: Session = Depends(get_db)):
    """GET /api/v1/incidents/{incident_id} - Detailed incident metadata, snapshot, actions, memory."""
    inc = db.get(Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    snapshots = db.scalars(
        select(InfrastructureSnapshot).where(InfrastructureSnapshot.incident_id == incident_id)
    ).all()
    actions = db.scalars(
        select(OperationalActionHistory)
        .where(OperationalActionHistory.incident_id == incident_id)
        .order_by(asc(OperationalActionHistory.timestamp))
    ).all()
    memories = db.scalars(
        select(InstitutionalMemoryVector).where(InstitutionalMemoryVector.incident_id == incident_id)
    ).all()

    return {
        "id": inc.id,
        "title": inc.title,
        "description": inc.description,
        "severity": inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
        "status": inc.status.value if hasattr(inc.status, "value") else str(inc.status),
        "service": inc.service,
        "region": inc.region,
        "start_time": inc.start_time.isoformat(),
        "end_time": inc.end_time.isoformat() if inc.end_time else None,
        "target_resource_id": inc.target_resource_id,
        "environment_fingerprint": inc.environment_fingerprint,
        "root_cause_summary": inc.root_cause_summary,
        "memory_status": inc.memory_status,
        "snapshots": [
            {
                "id": s.id,
                "db_version": s.db_version,
                "service_version": s.service_version,
                "topology": s.topology,
                "configuration": s.configuration,
                "dependencies": s.dependencies,
                "region": s.region,
                "snapshot_timestamp": s.snapshot_timestamp.isoformat(),
            } for s in snapshots
        ],
        "actions": [
            {
                "id": a.id,
                "actor": a.actor,
                "agent": a.agent,
                "command": a.command,
                "tool": a.tool,
                "target": a.target,
                "risk_level": a.risk_level,
                "reason": a.reason,
                "idempotency_key": a.idempotency_key,
                "result": a.result,
                "error_message": a.error_message,
                "timestamp": a.timestamp.isoformat(),
            } for a in actions
        ],
        "memories": [
            {
                "id": m.id,
                "title": m.title,
                "memory_type": m.memory_type,
                "content": m.content,
                "trust_level": m.trust_level.value if hasattr(m.trust_level, "value") else str(m.trust_level),
                "created_at": m.created_at.isoformat(),
            } for m in memories
        ]
    }

@router.get("/{incident_id}/evidence", response_model=List[Dict[str, Any]])
def get_incident_evidence(incident_id: str, db: Session = Depends(get_db)):
    """GET /api/v1/incidents/{incident_id}/evidence - Raw unredacted evidence."""
    inc = db.get(Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    evidence_list = db.scalars(
        select(IncidentEvidence)
        .where(IncidentEvidence.incident_id == incident_id)
        .order_by(asc(IncidentEvidence.captured_at))
    ).all()

    return [
        {
            "evidence_id": ev.id,
            "incident_id": ev.incident_id,
            "source": ev.source,
            "source_event_id": ev.source_event_id,
            "captured_at": ev.captured_at.isoformat(),
            "event_type": ev.event_type,
            "raw_payload": ev.raw_payload,
            "content_hash": ev.content_hash,
            "trust_level": ev.trust_level.value if hasattr(ev.trust_level, "value") else str(ev.trust_level),
        } for ev in evidence_list
    ]

@router.get("/{incident_id}/timeline", response_model=List[Dict[str, Any]])
def get_incident_timeline(incident_id: str, db: Session = Depends(get_db)):
    """GET /api/v1/incidents/{incident_id}/timeline - Chronological timeline events."""
    inc = db.get(Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    events = db.scalars(
        select(IncidentEvent)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(asc(IncidentEvent.event_timestamp), asc(IncidentEvent.event_source))
    ).all()

    return [
        {
            "id": evt.id,
            "timestamp": evt.event_timestamp.isoformat(),
            "source": evt.event_source,
            "event_type": evt.event_name,
            "payload": evt.payload,
        } for evt in events
    ]

@router.get("/{incident_id}/summary", response_model=Dict[str, Any])
def get_incident_summary(incident_id: str, db: Session = Depends(get_db)):
    """GET /api/v1/incidents/{incident_id}/summary - Structured summary built directly from database records."""
    inc = db.get(Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    events_count = len(inc.events)
    evidence_count = len(inc.evidence)
    actions = db.scalars(
        select(OperationalActionHistory).where(OperationalActionHistory.incident_id == incident_id)
    ).all()
    failed_actions = [a.command for a in actions if a.result == "FAILED"]
    success_actions = [a.command for a in actions if a.result == "SUCCESS"]

    return {
        "incident_id": inc.id,
        "title": inc.title,
        "service": inc.service,
        "region": inc.region,
        "severity": inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
        "status": inc.status.value if hasattr(inc.status, "value") else str(inc.status),
        "start_time": inc.start_time.isoformat(),
        "events_count": events_count,
        "evidence_count": evidence_count,
        "total_actions": len(actions),
        "failed_action_attempts": failed_actions,
        "successful_action_attempts": success_actions,
        "root_cause": inc.root_cause_summary or "Explicit root cause not provided in telemetry",
        "memory_status": inc.memory_status,
    }

@router.get("/{incident_id}/similar", response_model=SimilarIncidentsResponse)
def get_similar_incidents(
    incident_id: str,
    limit: int = Query(5, ge=1, le=20),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    include_failed_actions: bool = Query(True),
    db: Session = Depends(get_db)
):
    """GET /api/v1/incidents/{incident_id}/similar - Hybrid retrieval engine answering 'Have we seen something like this before?'"""
    try:
        return HistoricalRetrievalService.get_similar_incidents(
            db=db,
            incident_id=incident_id,
            limit=limit,
            min_score=min_score,
            include_failed_actions=include_failed_actions
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid retrieval failed: {e}")
