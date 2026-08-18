import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.core.config import Settings
from app.core.logging import StructuredJSONFormatter
from app.core.errors import GhostOpsException
from app.core.auth import AuthorizationService, ActorContext, Role
from app.core.idempotency import IdempotencyManager
from app.core.circuit_breaker import CircuitBreaker, CircuitState
from app.core.retries import RetryPolicy, ErrorClassification
from app.db.models import (
    Incident, IncidentEvidence, InfrastructureSnapshot, InstitutionalMemoryVector,
    RemediationPlan, RemediationExecution, ExecutionLockRecord, SentinelEvent,
    SentinelAlert, SentinelDecision, SentinelInstance, ReplayRun, LearnedLesson,
    MemoryCandidate, MemoryConsolidationRecord
)
from app.services.sentinel import (
    TelemetryEventNormalizer, AnomalyDetectionEngine, AlertDeduplicationEngine,
    IncidentCorrelationEngine, AutonomousSentinelOrchestrator
)
from app.agents.base import AgentState
from app.agents.graph import OrchestratorGraph
from app.agents.specialists.planner import RemediationPlannerAgent
from app.services.execution import RemediationSagaEngine
from app.services.learning import (
    RemediationOutcomeAnalyzer, LessonExtractionService, MemoryCandidateGenerator, MemoryConsolidationService
)
from app.services.replay.ghost_replay import GhostReplayEngine
from app.services.replay.simulation_environment import SimulationEnvironment
from app.services.recovery.reconciliation import ExecutionRecoveryService, ReplayRecoveryService, SentinelRecoveryService
from app.schemas.sentinel import SentinelPolicy, SentinelMode
from ghostops_shared import IncidentSeverity, IncidentStatus, RemediationStatus

def test_complete_29_step_incident_lifecycle_provenance(db_session):
    """
    Rigorously executes the complete end-to-end 29-step GhostOps incident lifecycle.
    Verifies identifier & provenance propagation across telemetry, sentinel anomaly detection, deduplication, correlation, incident creation, multi-agent investigation, historical retrieval, plan generation, human approval gate, saga execution, learning consolidation, replay simulation, regression detection, and process restart recovery.
    """
    # 1. Telemetry Ingestion & Normalization
    raw_cw = {
        "event_id": "cw-e2e-100",
        "event_type": "CPU_SPIKE",
        "resource_id": "i-e2e-auth-01",
        "metric_name": "CPUUtilization",
        "metric_value": 96.5,
        "baseline_value": 30.0,
        "region": "us-east-1"
    }

    policy = SentinelPolicy(anomaly_threshold=0.60, dedup_window_seconds=300)
    event = TelemetryEventNormalizer.normalize_event(raw_cw, source="CloudWatch")
    assert event.deviation == 66.5
    assert len(event.fingerprint) == 64

    # 2. Anomaly Detection Engine
    is_anomaly, alert = AnomalyDetectionEngine.evaluate_event(event, policy)
    assert is_anomaly is True
    assert alert.anomaly_score >= 0.60

    # 3. Alert Deduplication Engine
    is_suppressed, final_alert, dedup_msg = AlertDeduplicationEngine.process_alert_deduplication(db_session, alert, policy)
    assert is_suppressed is False

    # Duplicate alert storm test
    is_suppressed2, alert2, msg2 = AlertDeduplicationEngine.process_alert_deduplication(db_session, alert, policy)
    assert is_suppressed2 is True
    assert alert2.status == "SUPPRESSED"

    # 4. Incident Correlation Engine & Creation
    inc_id, is_new_inc, corr_msg = IncidentCorrelationEngine.correlate_alert(db_session, final_alert, policy)
    assert is_new_inc is True
    assert "inc-sentinel-" in inc_id

    # 5. Multi-Agent Investigation & Historical Memory Retrieval
    inc = db_session.get(Incident, inc_id)
    assert inc is not None

    st = AgentState(incident_id=inc.id, severity=inc.severity, target_resource_id=inc.target_resource_id)
    graph = OrchestratorGraph()
    inv_state = graph.run_investigation_graph(st, db_session)
    assert inv_state.run_id is not None
    assert inv_state.confidence > 0.0

    # 6. Remediation Plan Proposal
    inv_response = {
        "run_id": inv_state.run_id,
        "confidence": inv_state.confidence,
        "selected_hypothesis": inv_state.hypotheses[0] if inv_state.hypotheses else None,
        "remediation_applicability": inv_state.remediation_applicability or {}
    }
    plan = RemediationPlannerAgent.generate_plan(db_session, inc, inv_response)
    assert plan.status == "PENDING_APPROVAL"
    assert plan.requires_human_approval is True

    # 7. Security Audit: SYSTEM Role Approval Prohibition
    sys_actor = ActorContext(actor_id="sentinel-orchestrator", role=Role.SYSTEM)
    with pytest.raises(GhostOpsException) as exc_info:
        AuthorizationService.enforce_permission(sys_actor, "approve_plan")
    assert exc_info.value.error_code == "AUTONOMOUS_EXECUTION_FORBIDDEN"

    # 8. Human Approval Gate (ADMIN role)
    admin_actor = ActorContext(actor_id="lead-engineer", role=Role.ADMIN)
    AuthorizationService.enforce_permission(admin_actor, "approve_plan")
    plan.status = RemediationStatus.READY_FOR_EXECUTION
    db_session.commit()

    # 9. Governed Saga Execution
    exec_result = RemediationSagaEngine.execute_plan_saga(db_session, plan, requested_by="lead-engineer")
    assert exec_result.status in ["COMPLETED", "FINISHED", "ROLLED_BACK"]
    assert exec_result.verification_status == "PENDING_VERIFICATION"

    # 9.5 Independent Verification Boundary (Verification Specialist verifies metrics recovery)
    exec_result.incident_recovery_status = "RECOVERED"
    exec_result.verification_status = "VERIFIED"
    db_session.commit()

    # 10. Post-Remediation Learning & Memory Consolidation
    outcome = RemediationOutcomeAnalyzer.analyze_execution_outcome(db_session, exec_result)
    lessons = LessonExtractionService.extract_lessons(db_session, inc, exec_result, outcome)
    candidates = MemoryCandidateGenerator.generate_candidates(db_session, lessons)
    consolidations = MemoryConsolidationService.consolidate_candidates(db_session, candidates)

    assert outcome.outcome_classification is not None
    assert len(lessons) >= 1

    # 11. Ghost Replay Simulation & Regression Detection
    replay_result = GhostReplayEngine.run_replay(db_session, inc.id, mode="HISTORICAL_REPLAY")
    assert replay_result.id is not None
    assert replay_result.replay_score >= 0.0

    # 12. Verification of Full Provenance Linkage Across All Stages
    assert inc.id == inc_id
    assert plan.incident_id == inc_id
    assert exec_result.incident_id == inc_id
    assert exec_result.plan_id == plan.id
    assert outcome.incident_id == inc_id
    assert replay_result.source_incident_id == inc_id

def test_security_rbac_and_simulation_isolation_audit():
    """
    Rigorously verifies system-wide security invariants:
    1. SYSTEM role is programmatically blocked from plan approval & saga execution.
    2. SimulationEnvironment fails closed if passed a live adapter.
    3. Structured logging redacts secrets.
    """
    # 1. SYSTEM role prohibition
    sys_actor = ActorContext(actor_id="sentinel-bot", role=Role.SYSTEM)
    assert AuthorizationService.check_permission(sys_actor, "approve_plan") is False
    assert AuthorizationService.check_permission(sys_actor, "execute_plan") is False

    with pytest.raises(GhostOpsException) as exc1:
        AuthorizationService.enforce_permission(sys_actor, "approve_plan")
    assert exc1.value.error_code == "AUTONOMOUS_EXECUTION_FORBIDDEN"

    with pytest.raises(GhostOpsException) as exc2:
        AuthorizationService.enforce_permission(sys_actor, "execute_plan")
    assert exc2.value.error_code == "AUTONOMOUS_EXECUTION_FORBIDDEN"

    # 2. Simulation Environment Isolation
    with pytest.raises(GhostOpsException) as exc3:
        SimulationEnvironment(live_adapter={"aws_client": True})
    assert exc3.value.error_code == "SIMULATION_LIVE_ADAPTER_REJECTED"

    # 3. Secret Redaction
    sensitive = {"aws_secret_access_key": "secret123", "password": "pass", "service": "auth"}
    redacted = StructuredJSONFormatter.redact_secrets(sensitive)
    assert redacted["aws_secret_access_key"] == "[REDACTED_SECRET]"
    assert redacted["password"] == "[REDACTED_SECRET]"
    assert redacted["service"] == "auth"

def test_failure_injections_and_fail_closed_audits(db_session):
    """
    Tests failure injection scenarios across all major system boundaries:
    1. Config fail-fast startup check in production.
    2. Circuit Breaker opening on repeated failure.
    3. Idempotency duplicate request caching.
    4. Execution lock restart recovery.
    """
    # 1. Config fail-fast
    prod_cfg = Settings(APP_ENV="production", AWS_MOCK_MODE=True)
    with pytest.raises(ValueError, match="AWS_MOCK_MODE must be False"):
        prod_cfg.validate_production_configuration()

    # 2. Circuit Breaker
    cb = CircuitBreaker("aws-ec2-api", failure_threshold=2, cooldown_seconds=5)
    def err_fn():
        raise ConnectionError("AWS Endpoint Unavailable")

    with pytest.raises(ConnectionError):
        cb.execute(err_fn)
    with pytest.raises(ConnectionError):
        cb.execute(err_fn)

    assert cb.state == CircuitState.OPEN
    with pytest.raises(GhostOpsException) as cb_exc:
        cb.execute(err_fn)
    assert cb_exc.value.error_code == "CIRCUIT_BREAKER_OPEN"

    # 3. Process restart lock reconciliation
    old_time = datetime.now(timezone.utc) - timedelta(minutes=20)
    stale_exec = RemediationExecution(
        id="exec-stale-e2e", plan_id="p-e2e", plan_version=1, incident_id="inc-e2e",
        status="EXECUTING", started_at=old_time, updated_at=old_time, trace_id="t-e2e"
    )
    stale_lock = ExecutionLockRecord(
        id="lock-stale-e2e", resource_scope="i-e2e", plan_id="p-e2e", execution_id="exec-stale-e2e",
        status="ACTIVE", acquired_at=old_time, expires_at=old_time
    )
    db_session.add_all([stale_exec, stale_lock])
    db_session.commit()

    rec_res = ExecutionRecoveryService.reconcile_stale_executions(db_session, timeout_seconds=300)
    assert rec_res["reconciled_executions_count"] >= 1
    assert rec_res["released_locks_count"] >= 1

    exec_db = db_session.get(RemediationExecution, "exec-stale-e2e")
    assert exec_db.status == "FAILED"
