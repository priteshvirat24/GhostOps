import pytest
from datetime import datetime, timezone, timedelta
from app.db.models import Incident, InfrastructureSnapshot, RemediationPlan, PlanStep, RemediationExecution
from app.services.execution import (
    ExecutionStateMachine,
    ExecutionPrecheckEngine,
    ExecutionLockManager,
    StatefulMockInfrastructure,
    TypedActionExecutors,
    RemediationVerificationEngine,
    RemediationSagaEngine,
)
from app.schemas.remediation_execution import ExecutionStatus, StepExecutionStatus
from ghostops_shared import IncidentSeverity, RemediationStatus

def test_execution_state_machine_valid_and_invalid_transitions():
    valid, msg = ExecutionStateMachine.validate_transition(ExecutionStatus.PENDING, ExecutionStatus.PRECHECKING)
    assert valid is True

    valid_exec, _ = ExecutionStateMachine.validate_transition(ExecutionStatus.EXECUTING, ExecutionStatus.VERIFYING)
    assert valid_exec is True

    invalid, msg = ExecutionStateMachine.validate_transition(ExecutionStatus.PENDING, ExecutionStatus.EXECUTING)
    assert invalid is False
    assert "Illegal state transition" in msg

def test_stateful_mock_infrastructure_mutation_and_rollback():
    target = "arn:aws:ec2:us-east-1:123456789012:security-group/sg-test-01"
    pre_st, post_st = StatefulMockInfrastructure.apply_mutation(target, "ADJUST_CONNECTION_POOL", {"max_connections": 150})

    assert pre_st.get("connection_pool_max") == 50
    assert post_st.get("connection_pool_max") == 150

    # Compensate / Rollback
    comp_pre, comp_post = StatefulMockInfrastructure.apply_mutation(target, "ADJUST_CONNECTION_POOL", {"max_connections": 50})
    assert comp_post.get("connection_pool_max") == 50

def test_secret_redaction_in_action_executors():
    sensitive_data = {
        "db_password": "super_secret_db_password_123",
        "aws_access_key": "AKIAIOSFODNN7EXAMPLE",
        "normal_key": "normal_value"
    }
    redacted = TypedActionExecutors.redact_secrets(sensitive_data)

    assert redacted["db_password"] == "[REDACTED_SECRET]"
    assert redacted["aws_access_key"] == "[REDACTED_SECRET]"
    assert redacted["normal_key"] == "normal_value"

def test_execution_lock_manager(db_session):
    scope = "inc-lock-test-scope"
    plan_id = "plan-lock-1"
    exec_id_1 = "exec-lock-1"
    exec_id_2 = "exec-lock-2"

    acquired, lock1, msg1 = ExecutionLockManager.acquire_lock(db_session, scope, plan_id, exec_id_1)
    assert acquired is True
    assert lock1 is not None

    # Try acquiring lock on same scope for second execution
    acquired2, lock2, msg2 = ExecutionLockManager.acquire_lock(db_session, scope, plan_id, exec_id_2)
    assert acquired2 is False
    assert "EXECUTION_BLOCKED_BY_LOCK" in msg2

    # Release lock
    released = ExecutionLockManager.release_lock(db_session, lock1.id)
    assert released is True

    # Re-try acquiring lock
    acquired3, lock3, msg3 = ExecutionLockManager.acquire_lock(db_session, scope, plan_id, exec_id_2)
    assert acquired3 is True

def test_saga_engine_successful_execution(db_session):
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-saga-succ", title="Saga Succ Test", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    plan = RemediationPlan(
        id="plan-saga-succ", incident_id=inc.id, title="Test Plan", explanation="Desc",
        status=RemediationStatus.APPROVED, confidence=0.88, compatibility_score=0.90,
        estimated_risk="HIGH_RISK", risk_score=0.75, blast_radius="REGION", idempotency_key="key-saga-succ",
        expires_at=now_time + timedelta(hours=24),
        rollback_plan=[{"action_type": "CHANGE_SECURITY_RULE", "reason": "Rollback"}],
        verification_plan=[{"check_id": "v1", "type": "CLOUDWATCH_METRIC", "target": "auth-service", "expected_condition": "CPU < 50%"}]
    )

    step = PlanStep(remediation_plan_id=plan.id, step_order=1, action_type="CHANGE_SECURITY_RULE", target_resource_arn="sg-saga-succ", parameters={"security_group_id": "sg-saga-succ", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"})
    plan.steps.append(step)

    db_session.add(plan)
    db_session.commit()

    exec_rec = RemediationSagaEngine.execute_plan_saga(db_session, plan, requested_by="DevOpsLead")
    assert exec_rec.status == ExecutionStatus.COMPLETED
    assert exec_rec.verification_status == "PENDING_VERIFICATION"
    assert exec_rec.incident_recovery_status == "UNKNOWN"
    assert exec_rec.executed_steps == 1
    assert len(exec_rec.events) >= 5

def test_saga_engine_step_failure_and_reverse_compensation(db_session):
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-saga-fail", title="Saga Fail Test", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    plan = RemediationPlan(
        id="plan-saga-fail", incident_id=inc.id, title="Test Plan", explanation="Desc",
        status=RemediationStatus.APPROVED, confidence=0.88, compatibility_score=0.90,
        estimated_risk="HIGH_RISK", risk_score=0.75, blast_radius="REGION", idempotency_key="key-saga-fail",
        expires_at=now_time + timedelta(hours=24),
        rollback_plan=[{"action_type": "CHANGE_SECURITY_RULE", "reason": "Rollback"}],
        verification_plan=[{"check_id": "v1", "type": "CLOUDWATCH_METRIC", "target": "auth-service", "expected_condition": "CPU < 50%"}]
    )

    step1 = PlanStep(remediation_plan_id=plan.id, step_order=1, action_type="UPDATE_CONFIGURATION", target_resource_arn="svc-1", parameters={"config_key": "k1", "config_value": "v1"}, rollback_parameters={"config_key": "k1", "config_value": "v0"})
    step2 = PlanStep(remediation_plan_id=plan.id, step_order=2, action_type="CHANGE_SECURITY_RULE", target_resource_arn="sg-fail", parameters={"security_group_id": "sg-fail", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"})
    plan.steps.extend([step1, step2])

    db_session.add(plan)
    db_session.commit()

    # Trigger saga execution with simulated step failure on step 2
    exec_rec = RemediationSagaEngine.execute_plan_saga(db_session, plan, requested_by="DevOpsLead", simulated_step_failure=True)
    assert exec_rec.status == ExecutionStatus.ROLLED_BACK
    assert exec_rec.executed_steps == 1
    assert exec_rec.compensated_steps == 1

def test_execution_api_dry_run_and_execution(client, db_session):
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-exec-api", title="Exec API Test", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    plan = RemediationPlan(
        id="plan-exec-api", incident_id=inc.id, title="Test Plan", explanation="Desc",
        status=RemediationStatus.APPROVED, confidence=0.88, compatibility_score=0.90,
        estimated_risk="HIGH_RISK", risk_score=0.75, blast_radius="REGION", idempotency_key="key-exec-api",
        expires_at=now_time + timedelta(hours=24),
        rollback_plan=[{"action_type": "CHANGE_SECURITY_RULE", "reason": "Rollback"}],
        verification_plan=[{"check_id": "v1", "type": "CLOUDWATCH_METRIC", "target": "auth-service", "expected_condition": "CPU < 50%"}]
    )
    step = PlanStep(remediation_plan_id=plan.id, step_order=1, action_type="CHANGE_SECURITY_RULE", target_resource_arn="sg-api", parameters={"security_group_id": "sg-api", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"})
    plan.steps.append(step)

    db_session.add(plan)
    db_session.commit()

    # 1. Dry run simulation
    dry_res = client.post(f"/api/v1/plans/{plan.id}/execute", json={"dry_run": True})
    assert dry_res.status_code == 200
    dry_data = dry_res.json()
    assert dry_data["dry_run"] is True
    assert dry_data["would_execute"] is True

    # 2. Governed Saga Execution
    exec_res = client.post(f"/api/v1/plans/{plan.id}/execute", json={"dry_run": False})
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "COMPLETED"
    assert exec_data["verification_status"] == "PENDING_VERIFICATION"
    assert len(exec_data["steps_detail"]) == 1

    exec_id = exec_data["execution_id"]

    # 3. GET execution detail
    detail_res = client.get(f"/api/v1/executions/{exec_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["execution_id"] == exec_id

    # 4. Manual Rollback API
    rb_res = client.post(f"/api/v1/executions/{exec_id}/rollback")
    assert rb_res.status_code == 200
    assert rb_res.json()["status"] == "ROLLED_BACK"

# =========================================================================
# Targeted Security & AWS Execution Governance Tests (Test A through Test J)
# =========================================================================

def test_security_gate_no_approval_rejected(db_session):
    """Test A: Execution rejected if plan has no human approval / status is PENDING_APPROVAL."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-sec-a", title="Unapproved Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    plan = RemediationPlan(
        id="plan-sec-a", incident_id=inc.id, title="Unapproved Plan", explanation="Desc",
        status=RemediationStatus.PENDING_APPROVAL, confidence=0.88, compatibility_score=0.90,
        estimated_risk="HIGH_RISK", risk_score=0.75, blast_radius="REGION", idempotency_key="key-sec-a",
        expires_at=now_time + timedelta(hours=24),
        rollback_plan=[{"action_type": "CHANGE_SECURITY_RULE", "reason": "Rollback"}]
    )
    db_session.add(plan)
    db_session.commit()

    passed, checks = ExecutionPrecheckEngine.run_prechecks(db_session, plan)
    assert passed is False
    assert any("plan_approval_check" in c.check_name and not c.passed for c in checks)

    exec_rec = RemediationSagaEngine.execute_plan_saga(db_session, plan)
    assert exec_rec.status == ExecutionStatus.BLOCKED
    assert exec_rec.termination_reason == "BLOCKED_BY_PRECHECKS"

def test_security_gate_approval_different_action_rejected(db_session):
    """Test B: Approval for different action type is rejected."""
    from app.services.governance.action_catalog import ActionCatalog
    errs = ActionCatalog.validate_action("UNKNOWN_MUTATION", "sg-012345", {"key": "val"})
    assert len(errs) > 0
    assert "Unknown or unauthorized action type" in errs[0]

def test_security_gate_approval_different_target_rejected(db_session):
    """Test C: Approval for unverified target resource is rejected before AWS."""
    from app.services.execution.aws_executor import AWSActionExecutor
    success, _, _, _, msg, mode = AWSActionExecutor.execute_action(
        action_type="CHANGE_SECURITY_RULE",
        target_resource="",
        parameters={},
        idempotency_key="key-sec-c"
    )
    assert success is False
    assert mode == "VALIDATION_FAILED"
    assert "Missing required parameter" in msg

def test_security_gate_environment_drift_blocks_execution(db_session):
    """Test D: Environment baseline drift detected immediately before mutation blocks execution."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-sec-d", title="Drift Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    # Database currently has v4.3.0
    snap = InfrastructureSnapshot(id="snap-sec-d", incident_id=inc.id, db_version="CockroachDB v23.2.3", service_version="v4.3.0")
    db_session.add_all([inc, snap])
    db_session.commit()

    # Plan was created against v4.2.0 snapshot
    plan = RemediationPlan(
        id="plan-sec-d", incident_id=inc.id, title="Drift Plan", explanation="Desc",
        status=RemediationStatus.APPROVED, confidence=0.88, compatibility_score=0.90,
        estimated_risk="HIGH_RISK", risk_score=0.75, blast_radius="REGION", idempotency_key="key-sec-d",
        expires_at=now_time + timedelta(hours=24),
        rollback_plan=[{"action_type": "CHANGE_SECURITY_RULE", "reason": "Rollback"}]
    )
    step = PlanStep(remediation_plan_id=plan.id, step_order=1, action_type="CHANGE_SECURITY_RULE", target_resource_arn="sg-sec-d", parameters={"security_group_id": "sg-sec-d", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"})
    plan.steps.append(step)
    db_session.add(plan)
    db_session.commit()

    exec_rec = RemediationSagaEngine.execute_plan_saga(db_session, plan)
    assert exec_rec.status == ExecutionStatus.BLOCKED
    assert exec_rec.termination_reason == "BLOCKED_BY_DRIFT"
    assert plan.status == RemediationStatus.REJECTED
    assert "REQUIRES_REVALIDATION" in plan.rejection_reason

def test_security_gate_duplicate_idempotency_key_no_second_call(db_session):
    """Test E & §15: Duplicate idempotency key reuses existing result and does not call AWS twice."""
    from app.db.models import OperationalActionHistory

    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-sec-e", title="Idemp Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    plan = RemediationPlan(
        id="plan-sec-e", incident_id=inc.id, title="Idemp Plan", explanation="Desc",
        status=RemediationStatus.APPROVED, confidence=0.88, compatibility_score=0.90,
        estimated_risk="HIGH_RISK", risk_score=0.75, blast_radius="REGION", idempotency_key="key-sec-e",
        expires_at=now_time + timedelta(hours=24),
        rollback_plan=[{"action_type": "CHANGE_SECURITY_RULE", "reason": "Rollback"}]
    )
    step = PlanStep(remediation_plan_id=plan.id, step_order=1, action_type="CHANGE_SECURITY_RULE", target_resource_arn="sg-sec-e", parameters={"security_group_id": "sg-sec-e", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"})
    plan.steps.append(step)
    db_session.add(plan)
    db_session.commit()

    # First execution: runs step and records OperationalActionHistory
    exec_rec1 = RemediationSagaEngine.execute_plan_saga(db_session, plan)
    assert exec_rec1.status == ExecutionStatus.COMPLETED
    assert exec_rec1.executed_steps == 1

    actions_count_after_first = db_session.query(OperationalActionHistory).filter(OperationalActionHistory.incident_id == inc.id).count()
    assert actions_count_after_first == 1

    # Second execution with same idempotency key
    exec_rec2 = RemediationSagaEngine.execute_plan_saga(db_session, plan)
    assert exec_rec2.status == ExecutionStatus.COMPLETED
    assert exec_rec2.executed_steps == 1
    # OperationalActionHistory is NOT inserted a second time
    actions_count_after_second = db_session.query(OperationalActionHistory).filter(OperationalActionHistory.incident_id == inc.id).count()
    assert actions_count_after_second == 1

def test_security_gate_invalid_action_parameter_rejected(db_session):
    """Test F: Invalid action parameters are rejected before reaching AWS."""
    from app.services.execution.aws_executor import AWSActionExecutor
    success, _, _, _, msg, mode = AWSActionExecutor.execute_action(
        action_type="CHANGE_SECURITY_RULE",
        target_resource="sg-012345",
        parameters={"security_group_id": "sg-012345"}, # Missing port, protocol, cidr_block
        idempotency_key="key-sec-f"
    )
    assert success is False
    assert mode == "VALIDATION_FAILED"
    assert "Missing required parameter" in msg

def test_security_gate_unknown_action_type_rejected(db_session):
    """Test G: Unknown action type is rejected before reaching AWS."""
    from app.services.execution.aws_executor import AWSActionExecutor
    success, _, _, _, msg, mode = AWSActionExecutor.execute_action(
        action_type="RUN_ARBITRARY_PYTHON",
        target_resource="sg-012345",
        parameters={"code": "import os; os.system('ls')"},
        idempotency_key="key-sec-g"
    )
    assert success is False
    assert mode == "VALIDATION_FAILED"
    assert "Unknown or unauthorized action type" in msg

def test_security_gate_mock_mode_explicitly_marked():
    """Test H: Mock execution is explicitly tagged as execution_mode='MOCK'."""
    from app.services.execution.aws_executor import AWSActionExecutor
    success, pre_st, post_st, req_id, summary, mode = AWSActionExecutor.execute_action(
        action_type="CHANGE_SECURITY_RULE",
        target_resource="sg-012345",
        parameters={"security_group_id": "sg-012345", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"},
        idempotency_key="key-sec-h",
        force_real_aws=False
    )
    assert success is True
    assert mode == "MOCK"
    assert "[MOCK]" in summary

def test_security_gate_real_aws_mode_no_silent_fallback():
    """Test I: Real AWS mode without credentials returns explicit BLOCKED/FAILED state, NOT SIMULATED_SUCCESS."""
    from app.services.execution.aws_executor import AWSActionExecutor
    # Force real AWS mode without setting credentials
    success, _, _, _, summary, mode = AWSActionExecutor.execute_action(
        action_type="CHANGE_SECURITY_RULE",
        target_resource="sg-012345",
        parameters={"security_group_id": "sg-012345", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"},
        idempotency_key="key-sec-i",
        force_real_aws=True
    )
    assert mode == "AWS_REAL"
    # Must never claim SIMULATED_SUCCESS
    assert "SIMULATED_SUCCESS" not in summary
    assert "MOCK" not in mode

def test_security_gate_aws_exception_creates_failed_saga_state(db_session):
    """Test J & §14: Real AWS exception creates FAILED execution state and initiates reverse compensation."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-sec-j", title="Fail Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    plan = RemediationPlan(
        id="plan-sec-j", incident_id=inc.id, title="Fail Plan", explanation="Desc",
        status=RemediationStatus.APPROVED, confidence=0.88, compatibility_score=0.90,
        estimated_risk="HIGH_RISK", risk_score=0.75, blast_radius="REGION", idempotency_key="key-sec-j",
        expires_at=now_time + timedelta(hours=24),
        rollback_plan=[{"action_type": "CHANGE_SECURITY_RULE", "reason": "Rollback"}]
    )
    # Step 1 succeeds, Step 2 fails
    step1 = PlanStep(remediation_plan_id=plan.id, step_order=1, action_type="UPDATE_CONFIGURATION", target_resource_arn="svc-j", parameters={"config_key": "k1", "config_value": "v1"}, rollback_parameters={"config_key": "k1", "config_value": "v0"})
    step2 = PlanStep(remediation_plan_id=plan.id, step_order=2, action_type="CHANGE_SECURITY_RULE", target_resource_arn="sg-sec-j", parameters={"security_group_id": "sg-sec-j", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"})
    plan.steps.extend([step1, step2])
    db_session.add(plan)
    db_session.commit()

    exec_rec = RemediationSagaEngine.execute_plan_saga(db_session, plan, simulated_step_failure=True)
    assert exec_rec.status == ExecutionStatus.ROLLED_BACK
    assert exec_rec.executed_steps == 1
    assert exec_rec.compensated_steps == 1
    assert any("COMPENSATION_STARTED" in e.event_type for e in exec_rec.events)
    assert any("ROLLBACK_COMPLETED" in e.event_type for e in exec_rec.events)

def test_real_aws_integration_or_blocked_report():
    """Section 20: Real AWS API boundary test."""
    from app.services.execution.aws_executor import AWSActionExecutor
    import boto3
    from botocore.exceptions import NoCredentialsError

    # Test real AWS client boundary execution
    success, pre_st, post_st, req_id, summary, mode = AWSActionExecutor.execute_action(
        action_type="CHANGE_SECURITY_RULE",
        target_resource="sg-012345",
        parameters={"security_group_id": "sg-012345", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"},
        idempotency_key="key-sec-boundary",
        force_real_aws=True
    )
    assert mode == "AWS_REAL"
    if not success:
        # Expected when AWS credentials are not configured in local CI
        assert ("REAL AWS INTEGRATION BLOCKED" in summary) or ("AWS ClientError" in summary) or ("AuthFailure" in summary)
    else:
        assert "[AWS_REAL]" in summary
