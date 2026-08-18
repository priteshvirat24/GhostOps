import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import (
    SentinelInstance,
    SentinelEvent as DBSentinelEvent,
    SentinelAlert as DBSentinelAlert,
    SentinelDecision as DBSentinelDecision,
    SentinelRun as DBSentinelRun,
    SentinelPolicy as DBSentinelPolicy,
    Incident
)
from app.schemas.sentinel import (
    SentinelStatus,
    SentinelMode,
    SentinelEventResponse,
    SentinelHealth,
    SentinelMetrics,
    SentinelPolicy,
    SentinelEvent,
    SentinelAlert
)
from app.services.sentinel.event_normalizer import TelemetryEventNormalizer
from app.services.sentinel.anomaly_engine import AnomalyDetectionEngine
from app.services.sentinel.deduplication_engine import AlertDeduplicationEngine
from app.services.sentinel.correlator import IncidentCorrelationEngine
from app.agents.base import AgentState
from app.agents.graph import OrchestratorGraph
from app.agents.specialists.planner import RemediationPlannerAgent
from app.services.replay.ghost_replay import GhostReplayEngine
from app.core.logging import logger

class AutonomousSentinelOrchestrator:
    """
    Autonomous Sentinel Orchestrator for GhostOps Stage 9.
    Executes continuous monitoring cycles, normalizes telemetry, computes anomaly scores, suppresses duplicate alerts, correlates incidents, and orchestrates Stage 4 investigation, Stage 8 ghost replay, and Stage 5 plan proposals within strict policy budgets.
    """

    _STATE: Dict[str, Any] = {
        "status": SentinelStatus.STOPPED,
        "mode": SentinelMode.DETECT_INVESTIGATE_AND_PLAN,
        "enabled": True,
        "poll_interval_seconds": 30,
        "last_heartbeat_at": datetime.now(timezone.utc),
        "consecutive_errors": 0,
        "events_processed": 0,
        "alerts_created": 0,
        "alerts_suppressed": 0,
        "incidents_correlated": 0,
        "investigations_triggered": 0,
        "plans_created": 0,
        "policy": SentinelPolicy()
    }

    @classmethod
    def get_status(cls, db: Session) -> SentinelHealth:
        now_str = datetime.now(timezone.utc).isoformat()
        inst = db.query(SentinelInstance).filter(SentinelInstance.sentinel_id == "sentinel-primary").first()

        status_val = cls._STATE["status"]
        mode_val = cls._STATE["mode"]
        if inst:
            inst.last_heartbeat_at = datetime.now(timezone.utc)
            db.commit()

        metrics = SentinelMetrics(
            events_processed=cls._STATE["events_processed"],
            alerts_created=cls._STATE["alerts_created"],
            alerts_suppressed=cls._STATE["alerts_suppressed"],
            incidents_correlated=cls._STATE["incidents_correlated"],
            investigations_triggered=cls._STATE["investigations_triggered"],
            plans_created=cls._STATE["plans_created"],
            consecutive_errors=cls._STATE["consecutive_errors"],
            uptime_seconds=3600.0
        )

        return SentinelHealth(
            sentinel_id="sentinel-primary",
            status=status_val,
            mode=mode_val,
            enabled=cls._STATE["enabled"],
            last_heartbeat_at=now_str,
            poll_interval_seconds=cls._STATE["poll_interval_seconds"],
            metrics=metrics,
            active_policy=cls._STATE["policy"]
        )

    @classmethod
    def start_sentinel(cls, db: Session, mode: str = SentinelMode.DETECT_INVESTIGATE_AND_PLAN, poll_interval: int = 30) -> SentinelHealth:
        cls._STATE["status"] = SentinelStatus.RUNNING
        cls._STATE["mode"] = mode
        cls._STATE["poll_interval_seconds"] = poll_interval
        cls._STATE["consecutive_errors"] = 0

        inst = db.query(SentinelInstance).filter(SentinelInstance.sentinel_id == "sentinel-primary").first()
        if not inst:
            inst = SentinelInstance(
                sentinel_id="sentinel-primary",
                name="GhostOps Primary Sentinel",
                status=SentinelStatus.RUNNING,
                mode=mode,
                enabled=True,
                poll_interval_seconds=poll_interval
            )
            db.add(inst)
        else:
            inst.status = SentinelStatus.RUNNING
            inst.mode = mode
            inst.poll_interval_seconds = poll_interval

        db.commit()
        logger.info(f"[Sentinel] Autonomous Sentinel started in mode '{mode}' with poll interval {poll_interval}s.")
        return cls.get_status(db)

    @classmethod
    def stop_sentinel(cls, db: Session, reason: str = "User requested stop") -> SentinelHealth:
        cls._STATE["status"] = SentinelStatus.STOPPED
        inst = db.query(SentinelInstance).filter(SentinelInstance.sentinel_id == "sentinel-primary").first()
        if inst:
            inst.status = SentinelStatus.STOPPED
            db.commit()
        logger.info(f"[Sentinel] Autonomous Sentinel stopped: {reason}")
        return cls.get_status(db)

    @classmethod
    def pause_sentinel(cls, db: Session, duration_seconds: int = 300, reason: str = "User requested pause") -> SentinelHealth:
        cls._STATE["status"] = SentinelStatus.PAUSED
        inst = db.query(SentinelInstance).filter(SentinelInstance.sentinel_id == "sentinel-primary").first()
        if inst:
            inst.status = SentinelStatus.PAUSED
            db.commit()
        logger.info(f"[Sentinel] Autonomous Sentinel paused for {duration_seconds}s: {reason}")
        return cls.get_status(db)

    @classmethod
    def resume_sentinel(cls, db: Session, reason: str = "User requested resume") -> SentinelHealth:
        cls._STATE["status"] = SentinelStatus.RUNNING
        inst = db.query(SentinelInstance).filter(SentinelInstance.sentinel_id == "sentinel-primary").first()
        if inst:
            inst.status = SentinelStatus.RUNNING
            db.commit()
        logger.info(f"[Sentinel] Autonomous Sentinel resumed: {reason}")
        return cls.get_status(db)

    @classmethod
    def update_policy(cls, db: Session, policy: SentinelPolicy) -> SentinelPolicy:
        cls._STATE["policy"] = policy
        logger.info(f"[Sentinel] Active policy updated: severity threshold={policy.severity_threshold}, anomaly threshold={policy.anomaly_threshold}")
        return policy

    @classmethod
    def process_telemetry_event(cls, db: Session, raw_payload: Dict[str, Any], source: str = "CloudWatch") -> SentinelEventResponse:
        cls._STATE["events_processed"] += 1
        policy: SentinelPolicy = cls._STATE["policy"]

        # 1. Telemetry Event Normalization
        event = TelemetryEventNormalizer.normalize_event(raw_payload, source)

        db_event = DBSentinelEvent(
            event_id=event.event_id,
            sentinel_id=event.sentinel_id,
            source=event.source,
            event_type=event.event_type,
            resource_id=event.resource_id,
            resource_type=event.resource_type,
            timestamp=datetime.now(timezone.utc),
            severity=event.severity,
            metric_name=event.metric_name,
            metric_value=event.metric_value,
            baseline_value=event.baseline_value,
            deviation=event.deviation,
            region=event.region,
            fingerprint=event.fingerprint,
            payload_hash=event.payload_hash,
            correlation_key=event.correlation_key,
            deduplication_key=event.deduplication_key,
            suppressed=False,
            processed=True
        )
        db.add(db_event)
        db.commit()

        # 2. Anomaly Detection Engine
        is_anomaly, alert = AnomalyDetectionEngine.evaluate_event(event, policy)
        if not is_anomaly or not alert:
            dec = DBSentinelDecision(
                decision_id=f"dec-{uuid.uuid4().hex[:10]}",
                sentinel_id=event.sentinel_id,
                event_id=event.event_id,
                decision_type="IGNORE",
                decision="IGNORE_EVENT",
                reason=f"Metric deviation {event.deviation} did not breach anomaly threshold {policy.anomaly_threshold}.",
                confidence=0.90,
                evidence_refs=[f"evt-{event.event_id}"]
            )
            db.add(dec)
            db.commit()
            return SentinelEventResponse(
                accepted=True,
                event_id=event.event_id,
                fingerprint=event.fingerprint,
                alert_created=False,
                decision="IGNORED_BELOW_THRESHOLD"
            )

        # 3. Alert Deduplication Engine
        is_suppressed, final_alert, dedup_msg = AlertDeduplicationEngine.process_alert_deduplication(db, alert, policy)
        if is_suppressed:
            cls._STATE["alerts_suppressed"] += 1
            dec = DBSentinelDecision(
                decision_id=f"dec-{uuid.uuid4().hex[:10]}",
                sentinel_id=event.sentinel_id,
                event_id=event.event_id,
                decision_type="SUPPRESS",
                decision="SUPPRESS_DUPLICATE_ALERT",
                reason=dedup_msg,
                confidence=0.95,
                evidence_refs=[f"evt-{event.event_id}"]
            )
            db.add(dec)
            db.commit()
            return SentinelEventResponse(
                accepted=True,
                event_id=event.event_id,
                fingerprint=event.fingerprint,
                alert_created=False,
                decision="SUPPRESSED_DUPLICATE"
            )

        cls._STATE["alerts_created"] += 1

        # 4. Incident Correlation Engine
        inc_id, is_new_inc, corr_msg = IncidentCorrelationEngine.correlate_alert(db, alert, policy)
        cls._STATE["incidents_correlated"] += 1

        dec = DBSentinelDecision(
            decision_id=f"dec-{uuid.uuid4().hex[:10]}",
            sentinel_id=event.sentinel_id,
            event_id=event.event_id,
            incident_id=inc_id,
            decision_type="CREATE_INCIDENT" if is_new_inc else "CORRELATE",
            decision="CORRELATED_WITH_INCIDENT",
            reason=corr_msg,
            confidence=0.95,
            evidence_refs=[f"alt-{alert.alert_id}"]
        )
        db.add(dec)
        db.commit()

        # 5. Mode-based Autonomous Orchestration
        current_mode = cls._STATE["mode"]
        inv_response = {}
        if current_mode in [SentinelMode.DETECT_AND_INVESTIGATE, SentinelMode.DETECT_INVESTIGATE_AND_PLAN]:
            # Trigger Stage 4 Investigation
            if cls._STATE["investigations_triggered"] < policy.max_investigations_per_window:
                try:
                    inc = db.get(Incident, inc_id)
                    if inc:
                        st = AgentState(incident_id=inc.id, severity=inc.severity, target_resource_id=inc.target_resource_id)
                        graph = OrchestratorGraph()
                        final_state = graph.run_investigation_graph(st, db)
                        cls._STATE["investigations_triggered"] += 1

                        inv_response = {
                            "run_id": final_state.run_id,
                            "confidence": final_state.confidence,
                            "selected_hypothesis": final_state.hypotheses[0] if final_state.hypotheses else None,
                            "remediation_applicability": final_state.remediation_applicability or {}
                        }

                        dec_inv = DBSentinelDecision(
                            decision_id=f"dec-{uuid.uuid4().hex[:10]}",
                            sentinel_id=event.sentinel_id,
                            event_id=event.event_id,
                            incident_id=inc_id,
                            decision_type="TRIGGER_INVESTIGATION",
                            decision="TRIGGERED_STAGE4_INVESTIGATION",
                            reason=f"Autonomously triggered investigation for incident '{inc_id}'. Run ID: {final_state.run_id}",
                            confidence=final_state.confidence,
                            evidence_refs=[f"inv-{final_state.run_id}"]
                        )
                        db.add(dec_inv)
                        db.commit()

                        # Trigger Stage 8 Ghost Replay
                        GhostReplayEngine.run_replay(db, inc_id, mode="HISTORICAL_REPLAY")

                except Exception as ex:
                    logger.warning(f"[Sentinel] Investigation trigger note: {ex}")

        if current_mode == SentinelMode.DETECT_INVESTIGATE_AND_PLAN and policy.auto_plan_enabled:
            # Trigger Stage 5 Governed Remediation Planning Proposal
            if cls._STATE["plans_created"] < policy.max_incidents_per_window:
                try:
                    inc = db.get(Incident, inc_id)
                    if inc:
                        plan = RemediationPlannerAgent.generate_plan(db, inc, inv_response)
                        cls._STATE["plans_created"] += 1

                        dec_plan = DBSentinelDecision(
                            decision_id=f"dec-{uuid.uuid4().hex[:10]}",
                            sentinel_id=event.sentinel_id,
                            event_id=event.event_id,
                            incident_id=inc_id,
                            decision_type="CREATE_PLAN",
                            decision="CREATED_REMEDIATION_PLAN_PROPOSAL",
                            reason=f"Autonomously proposed Stage 5 plan '{plan.id}' (Status: {plan.status}). Requires Stage 5 human approval before execution.",
                            confidence=plan.confidence,
                            evidence_refs=[f"plan-{plan.id}"]
                        )
                        db.add(dec_plan)
                        db.commit()
                except Exception as ex:
                    logger.warning(f"[Sentinel] Plan generation trigger note: {ex}")

        return SentinelEventResponse(
            accepted=True,
            event_id=event.event_id,
            fingerprint=event.fingerprint,
            alert_created=True,
            incident_id=inc_id,
            decision=f"CORRELATED_MODE_{current_mode}"
        )
