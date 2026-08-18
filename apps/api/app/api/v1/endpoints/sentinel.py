from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import (
    SentinelInstance,
    SentinelEvent,
    SentinelAlert,
    SentinelDecision,
    SentinelRun,
    SentinelPolicy
)
from app.schemas.sentinel import (
    SentinelHealth,
    SentinelStartRequest,
    SentinelStopRequest,
    SentinelPauseRequest,
    SentinelResumeRequest,
    SentinelConfigurationRequest,
    SentinelPolicy as SentinelPolicySchema,
    SentinelEventResponse,
    SentinelEvent as SentinelEventSchema,
    SentinelAlert as SentinelAlertSchema,
    SentinelDecision as SentinelDecisionSchema,
    SentinelRun as SentinelRunSchema
)
from app.services.sentinel import AutonomousSentinelOrchestrator

router = APIRouter()

@router.get("/sentinel/status", response_model=SentinelHealth)
def get_sentinel_status(db: Session = Depends(get_db)):
    return AutonomousSentinelOrchestrator.get_status(db)

@router.post("/sentinel/start", response_model=SentinelHealth)
def start_sentinel(payload: SentinelStartRequest = SentinelStartRequest(), db: Session = Depends(get_db)):
    return AutonomousSentinelOrchestrator.start_sentinel(db, mode=payload.mode, poll_interval=payload.poll_interval_seconds)

@router.post("/sentinel/stop", response_model=SentinelHealth)
def stop_sentinel(payload: SentinelStopRequest = SentinelStopRequest(), db: Session = Depends(get_db)):
    return AutonomousSentinelOrchestrator.stop_sentinel(db, reason=payload.reason)

@router.post("/sentinel/pause", response_model=SentinelHealth)
def pause_sentinel(payload: SentinelPauseRequest = SentinelPauseRequest(), db: Session = Depends(get_db)):
    return AutonomousSentinelOrchestrator.pause_sentinel(db, duration_seconds=payload.duration_seconds, reason=payload.reason)

@router.post("/sentinel/resume", response_model=SentinelHealth)
def resume_sentinel(payload: SentinelResumeRequest = SentinelResumeRequest(), db: Session = Depends(get_db)):
    return AutonomousSentinelOrchestrator.resume_sentinel(db, reason=payload.reason)

@router.post("/sentinel/policy", response_model=SentinelPolicySchema)
def update_sentinel_policy(payload: SentinelPolicySchema, db: Session = Depends(get_db)):
    return AutonomousSentinelOrchestrator.update_policy(db, payload)

@router.post("/sentinel/ingest-event", response_model=SentinelEventResponse)
def ingest_telemetry_event(raw_payload: Dict[str, Any], source: str = "CloudWatch", db: Session = Depends(get_db)):
    return AutonomousSentinelOrchestrator.process_telemetry_event(db, raw_payload, source)

@router.get("/sentinel/events", response_model=List[SentinelEventSchema])
def list_sentinel_events(limit: int = 50, db: Session = Depends(get_db)):
    evts = db.query(SentinelEvent).order_by(SentinelEvent.created_at.desc()).limit(limit).all()
    res = []
    for e in evts:
        res.append(SentinelEventSchema(
            event_id=e.event_id,
            sentinel_id=e.sentinel_id,
            source=e.source,
            event_type=e.event_type,
            resource_id=e.resource_id,
            resource_type=e.resource_type,
            timestamp=e.timestamp.isoformat() if e.timestamp else "",
            severity=e.severity,
            metric_name=e.metric_name,
            metric_value=e.metric_value,
            baseline_value=e.baseline_value,
            deviation=e.deviation,
            region=e.region,
            fingerprint=e.fingerprint,
            payload_hash=e.payload_hash,
            correlation_key=e.correlation_key,
            deduplication_key=e.deduplication_key,
            suppressed=e.suppressed,
            suppression_reason=e.suppression_reason,
            processed=e.processed,
            incident_id=e.incident_id
        ))
    return res

@router.get("/sentinel/alerts", response_model=List[SentinelAlertSchema])
def list_sentinel_alerts(limit: int = 50, db: Session = Depends(get_db)):
    alts = db.query(SentinelAlert).order_by(SentinelAlert.created_at.desc()).limit(limit).all()
    res = []
    for a in alts:
        res.append(SentinelAlertSchema(
            alert_id=a.alert_id,
            sentinel_id=a.sentinel_id,
            event_id=a.event_id,
            fingerprint=a.fingerprint,
            resource_id=a.resource_id,
            severity=a.severity,
            anomaly_score=a.anomaly_score,
            confidence=a.confidence,
            status=a.status,
            deduplication_key=a.deduplication_key,
            correlation_key=a.correlation_key,
            first_seen_at=a.first_seen_at.isoformat() if a.first_seen_at else "",
            last_seen_at=a.last_seen_at.isoformat() if a.last_seen_at else "",
            occurrence_count=a.occurrence_count,
            suppressed_count=a.suppressed_count,
            incident_id=a.incident_id
        ))
    return res

@router.get("/sentinel/decisions", response_model=List[SentinelDecisionSchema])
def list_sentinel_decisions(limit: int = 50, db: Session = Depends(get_db)):
    decs = db.query(SentinelDecision).order_by(SentinelDecision.created_at.desc()).limit(limit).all()
    res = []
    for d in decs:
        res.append(SentinelDecisionSchema(
            decision_id=d.decision_id,
            sentinel_id=d.sentinel_id,
            event_id=d.event_id,
            incident_id=d.incident_id,
            decision_type=d.decision_type,
            decision=d.decision,
            reason=d.reason,
            confidence=d.confidence,
            evidence_refs=d.evidence_refs or [],
            policy_refs=d.policy_refs or [],
            created_at=d.created_at.isoformat() if d.created_at else ""
        ))
    return res

@router.get("/sentinel/runs", response_model=List[SentinelRunSchema])
def list_sentinel_runs(limit: int = 20, db: Session = Depends(get_db)):
    runs = db.query(SentinelRun).order_by(SentinelRun.started_at.desc()).limit(limit).all()
    res = []
    for r in runs:
        res.append(SentinelRunSchema(
            run_id=r.run_id,
            sentinel_id=r.sentinel_id,
            started_at=r.started_at.isoformat() if r.started_at else "",
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            events_seen=r.events_seen,
            events_normalized=r.events_normalized,
            alerts_created=r.alerts_created,
            alerts_suppressed=r.alerts_suppressed,
            incidents_created=r.incidents_created,
            investigations_triggered=r.investigations_triggered,
            replays_triggered=r.replays_triggered,
            plans_created=r.plans_created,
            errors=r.errors or [],
            termination_reason=r.termination_reason
        ))
    return res
