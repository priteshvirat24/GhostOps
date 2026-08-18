import pytest
import logging
import json
from datetime import datetime, timezone, timedelta
from app.core.config import Settings
from app.core.logging import StructuredJSONFormatter
from app.core.errors import GhostOpsException
from app.core.auth import AuthorizationService, ActorContext, Role
from app.core.idempotency import IdempotencyManager
from app.core.circuit_breaker import CircuitBreaker, CircuitState
from app.core.retries import RetryPolicy, ErrorClassification
from app.services.recovery.reconciliation import ExecutionRecoveryService, ReplayRecoveryService, SentinelRecoveryService
from app.services.replay.simulation_environment import SimulationEnvironment
from app.db.models import RemediationExecution, ExecutionLockRecord

def test_production_configuration_fail_fast():
    # Production without required secrets must fail
    invalid_prod = Settings(APP_ENV="production", AWS_MOCK_MODE=True)
    with pytest.raises(ValueError, match="AWS_MOCK_MODE must be False"):
        invalid_prod.validate_production_configuration()

def test_structured_json_logging():
    formatter = StructuredJSONFormatter()
    record = logging.LogRecord("ghostops", logging.INFO, "path.py", 10, "Test log message", (), None)
    record.request_id = "req-12345"
    record.incident_id = "inc-12345"

    output_str = formatter.format(record)
    data = json.loads(output_str)

    assert data["service"] == "ghostops-api"
    assert data["message"] == "Test log message"
    assert data["request_id"] == "req-12345"
    assert data["incident_id"] == "inc-12345"

def test_rbac_authorization_boundary():
    sys_actor = ActorContext(actor_id="sentinel-bot", role=Role.SYSTEM)
    admin_actor = ActorContext(actor_id="admin-user", role=Role.ADMIN)

    # SYSTEM permissions
    assert AuthorizationService.check_permission(sys_actor, "trigger_investigation") is True
    assert AuthorizationService.check_permission(sys_actor, "create_plan") is True
    assert AuthorizationService.check_permission(sys_actor, "approve_plan") is False
    assert AuthorizationService.check_permission(sys_actor, "execute_plan") is False

    # System actor prohibited from approving plan
    with pytest.raises(GhostOpsException) as exc_info:
        AuthorizationService.enforce_permission(sys_actor, "approve_plan")
    assert exc_info.value.error_code == "AUTONOMOUS_EXECUTION_FORBIDDEN"

    # ADMIN permissions
    assert AuthorizationService.check_permission(admin_actor, "approve_plan") is True
    assert AuthorizationService.check_permission(admin_actor, "execute_plan") is True

def test_idempotency_manager():
    IdempotencyManager.clear_cache()
    key = IdempotencyManager.generate_key("/api/v1/plans/plan-1/execute", {"dry_run": False})

    is_cached, payload = IdempotencyManager.check_idempotency(key)
    assert is_cached is False

    IdempotencyManager.record_idempotency(key, {"execution_id": "exec-99"})
    is_cached2, payload2 = IdempotencyManager.check_idempotency(key)

    assert is_cached2 is True
    assert payload2["execution_id"] == "exec-99"

def test_circuit_breaker():
    cb = CircuitBreaker("test-service", failure_threshold=2, cooldown_seconds=10)

    def failing_fn():
        raise ValueError("Service unavailable")

    with pytest.raises(ValueError):
        cb.execute(failing_fn)

    with pytest.raises(ValueError):
        cb.execute(failing_fn)

    assert cb.state == CircuitState.OPEN

    with pytest.raises(GhostOpsException) as exc_info:
        cb.execute(failing_fn)
    assert exc_info.value.error_code == "CIRCUIT_BREAKER_OPEN"

def test_retry_policy_classification():
    exc_transient = GhostOpsException(error_code="NETWORK_TIMEOUT", message="Timeout")
    exc_safety = GhostOpsException(error_code="PLAN_BLOCKED_BY_DRIFT", message="Drift")

    assert RetryPolicy.classify_exception(exc_transient) == ErrorClassification.TRANSIENT
    assert RetryPolicy.classify_exception(exc_safety) == ErrorClassification.SAFETY_BLOCK

def test_execution_restart_recovery(db_session):
    now_time = datetime.now(timezone.utc)
    old_time = now_time - timedelta(minutes=20)

    stale_exec = RemediationExecution(
        id="exec-stale-1", plan_id="p-1", plan_version=1, incident_id="inc-1",
        status="EXECUTING", started_at=old_time, updated_at=old_time, trace_id="t-1"
    )
    stale_lock = ExecutionLockRecord(
        id="lock-stale-1", resource_scope="i-ec2", plan_id="p-1", execution_id="exec-stale-1",
        status="ACTIVE", acquired_at=old_time, expires_at=old_time
    )
    db_session.add_all([stale_exec, stale_lock])
    db_session.commit()

    res = ExecutionRecoveryService.reconcile_stale_executions(db_session, timeout_seconds=300)
    assert res["reconciled_executions_count"] >= 1
    assert res["released_locks_count"] >= 1

    reconciled_exec = db_session.get(RemediationExecution, "exec-stale-1")
    assert reconciled_exec.status == "FAILED"
    assert "RECONCILED" in reconciled_exec.termination_reason

def test_simulation_environment_live_adapter_rejection():
    # SimulationEnvironment must fail closed if a live adapter is supplied
    with pytest.raises(GhostOpsException) as exc_info:
        SimulationEnvironment(live_adapter={"aws_client": True})
    assert exc_info.value.error_code == "SIMULATION_LIVE_ADAPTER_REJECTED"

def test_secret_redaction():
    sensitive_dict = {
        "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "db_password": "supersecretpassword123",
        "service_name": "auth-service"
    }

    redacted = StructuredJSONFormatter.redact_secrets(sensitive_dict)
    assert redacted["AWS_SECRET_ACCESS_KEY"] == "[REDACTED_SECRET]"
    assert redacted["authorization"] == "[REDACTED_SECRET]"
    assert redacted["db_password"] == "[REDACTED_SECRET]"
    assert redacted["service_name"] == "auth-service"

def test_stage10_health_ready_live_metrics_endpoints(client):
    # 1. Health
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200

    # 2. Ready
    res_ready = client.get("/api/v1/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "READY"

    # 3. Live
    res_live = client.get("/api/v1/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "LIVE"

    # 4. Metrics (Prometheus exposition format)
    res_metrics = client.get("/api/v1/metrics")
    assert res_metrics.status_code == 200
    assert "ghostops_incidents_total" in res_metrics.text
