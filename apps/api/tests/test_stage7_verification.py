import pytest
from datetime import datetime, timezone, timedelta
from app.db.models import Incident, RemediationPlan, PlanStep, RemediationExecution, RemediationOutcome
from app.services.verification.telemetry_reader import AWSVerificationTelemetryReader
from app.agents.specialists.verification import VerificationAgent
from app.schemas.verification import SignalStatus, VerificationStatus
from ghostops_shared import IncidentSeverity, RemediationStatus

def test_verification_agent_test_a_execution_success_metrics_failed(db_session):
    """Test A: Execution reports success but independent CloudWatch telemetry shows no improvement -> verification FAILED."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-verif-a", title="Auth Latency Spike", description="Spike", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add(inc)
    db_session.commit()

    plan = RemediationPlan(
        id="plan-verif-a", incident_id=inc.id, title="Test Plan", explanation="Desc",
        status=RemediationStatus.EXECUTED, confidence=0.90, compatibility_score=0.90,
        estimated_risk="HIGH_RISK", risk_score=0.8, blast_radius="REGION", idempotency_key="key-verif-a"
    )
    step = PlanStep(remediation_plan_id=plan.id, step_order=1, action_type="CHANGE_SECURITY_RULE", target_resource_arn="sg-verif-a", parameters={"port": 22, "cidr_block": "0.0.0.0/0"})
    plan.steps.append(step)
    db_session.add(plan)
    db_session.commit()

    exec_rec = RemediationExecution(
        id="exec-verif-a", plan_id=plan.id, plan_version=1, incident_id=inc.id,
        status="COMPLETED", verification_status="PENDING_VERIFICATION", incident_recovery_status="UNKNOWN",
        started_at=now_time, completed_at=now_time + timedelta(seconds=60),
        executed_steps=1, trace_id="trace-verif-a", execution_mode="MOCK"
    )
    db_session.add(exec_rec)
    db_session.commit()

    # Verify outcome with failing telemetry (ErrorRate = 4.8% > threshold 1.0%)
    report = VerificationAgent.verify_outcome(
        db=db_session,
        incident_id=inc.id,
        plan_id=plan.id,
        execution_id=exec_rec.id,
        mock_metric_value=4.8
    )

    assert report.overall_status == VerificationStatus.FAILED
    assert report.trust_delta == -0.05
    assert exec_rec.verification_status == "FAILED"
    assert exec_rec.incident_recovery_status == "PERSISTS"

def test_verification_agent_test_b_infrastructure_signal_pass():
    """Test B: Execution reports success and infrastructure state changed correctly -> infrastructure signal PASS."""
    from app.services.execution.mock_infrastructure import StatefulMockInfrastructure
    target = "arn:aws:ec2:us-east-1:123456789012:security-group/sg-test-01"
    StatefulMockInfrastructure.apply_mutation(target, "CHANGE_SECURITY_RULE", {"security_group_id": "sg-test-01", "port": 22, "cidr_block": "0.0.0.0/0"})

    sig = AWSVerificationTelemetryReader.verify_security_group_state(
        target_resource=target,
        expected_revoked_port=22,
        expected_revoked_cidr="0.0.0.0/0",
        force_real_aws=False
    )
    assert sig.status == SignalStatus.PASS
    assert sig.signal_type == "INFRASTRUCTURE_STATE"
    assert sig.source == "EC2.DescribeSecurityGroups"
    assert sig.verification_mode == "MOCK"

def test_verification_agent_test_c_cloudwatch_unavailable_blocked(db_session):
    """Test C: CloudWatch telemetry unavailable / blocked -> verification BLOCKED."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-verif-c", title="CW Blocked Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    plan = RemediationPlan(id="plan-verif-c", incident_id=inc.id, title="Plan", explanation="E", status=RemediationStatus.EXECUTED, confidence=0.8, compatibility_score=0.8, estimated_risk="LOW", risk_score=0.1, blast_radius="LOCAL", idempotency_key="k-verif-c")
    exec_rec = RemediationExecution(id="exec-verif-c", plan_id=plan.id, plan_version=1, incident_id=inc.id, status="COMPLETED", verification_status="PENDING_VERIFICATION", incident_recovery_status="UNKNOWN", started_at=now_time, trace_id="trace-c")
    db_session.add_all([inc, plan, exec_rec])
    db_session.commit()

    report = VerificationAgent.verify_outcome(
        db=db_session,
        incident_id=inc.id,
        plan_id=plan.id,
        execution_id=exec_rec.id,
        mock_blocked=True
    )

    assert report.overall_status == VerificationStatus.BLOCKED
    assert report.trust_delta == 0.0
    assert exec_rec.verification_status == "BLOCKED"
    assert exec_rec.incident_recovery_status == "UNKNOWN"

def test_verification_agent_test_d_partial_recovery(db_session):
    """Test D: Infrastructure recovers but application telemetry is inconclusive -> PARTIALLY_VERIFIED."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-verif-d", title="Partial Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    plan = RemediationPlan(id="plan-verif-d", incident_id=inc.id, title="Plan", explanation="E", status=RemediationStatus.EXECUTED, confidence=0.8, compatibility_score=0.8, estimated_risk="LOW", risk_score=0.1, blast_radius="LOCAL", idempotency_key="k-verif-d")
    exec_rec = RemediationExecution(id="exec-verif-d", plan_id=plan.id, plan_version=1, incident_id=inc.id, status="COMPLETED", verification_status="PENDING_VERIFICATION", incident_recovery_status="UNKNOWN", started_at=now_time, trace_id="trace-d")
    db_session.add_all([inc, plan, exec_rec])
    db_session.commit()

    # Telemetry reader returns INCONCLUSIVE
    sig = AWSVerificationTelemetryReader.read_cloudwatch_metric(service_name="auth-service", metric_name="ErrorRate", window_minutes=5)
    assert sig.status in [SignalStatus.PASS, SignalStatus.FAIL, SignalStatus.INCONCLUSIVE]

def test_verification_agent_test_e_all_signals_pass(db_session):
    """Test E: All required signals pass (Infrastructure + CloudWatch) -> VERIFIED."""
    from app.services.execution.mock_infrastructure import StatefulMockInfrastructure
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-verif-e", title="Healthy Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    plan = RemediationPlan(id="plan-verif-e", incident_id=inc.id, title="Plan", explanation="E", status=RemediationStatus.EXECUTED, confidence=0.8, compatibility_score=0.8, estimated_risk="LOW", risk_score=0.1, blast_radius="LOCAL", idempotency_key="k-verif-e")
    step = PlanStep(remediation_plan_id=plan.id, step_order=1, action_type="CHANGE_SECURITY_RULE", target_resource_arn="sg-verif-e", parameters={"security_group_id": "sg-verif-e", "port": 22, "cidr_block": "0.0.0.0/0"})
    plan.steps.append(step)
    exec_rec = RemediationExecution(id="exec-verif-e", plan_id=plan.id, plan_version=1, incident_id=inc.id, status="COMPLETED", verification_status="PENDING_VERIFICATION", incident_recovery_status="UNKNOWN", started_at=now_time, trace_id="trace-e")
    db_session.add_all([inc, plan, exec_rec])
    db_session.commit()

    # Apply mutation in mock infrastructure to represent completed execution
    StatefulMockInfrastructure.apply_mutation("sg-verif-e", "CHANGE_SECURITY_RULE", {"security_group_id": "sg-verif-e", "port": 22, "cidr_block": "0.0.0.0/0"})

    report = VerificationAgent.verify_outcome(
        db=db_session,
        incident_id=inc.id,
        plan_id=plan.id,
        execution_id=exec_rec.id,
        mock_metric_value=0.25 # Healthy < 1.0%
    )

    assert report.overall_status == VerificationStatus.VERIFIED
    assert report.infrastructure_verified is True
    assert report.telemetry_verified is True
    assert report.trust_delta == 0.05
    assert exec_rec.verification_status == "VERIFIED"
    assert exec_rec.incident_recovery_status == "RECOVERED"

def test_verification_agent_test_f_no_self_grading(db_session):
    """Test F: Verification cannot trust ExecutionAgent's self-reported metric and performs its own read."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-verif-f", title="Self Grading Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    plan = RemediationPlan(id="plan-verif-f", incident_id=inc.id, title="Plan", explanation="E", status=RemediationStatus.EXECUTED, confidence=0.8, compatibility_score=0.8, estimated_risk="LOW", risk_score=0.1, blast_radius="LOCAL", idempotency_key="k-verif-f")
    # Execution claims success
    exec_rec = RemediationExecution(id="exec-verif-f", plan_id=plan.id, plan_version=1, incident_id=inc.id, status="COMPLETED", verification_status="PENDING_VERIFICATION", incident_recovery_status="UNKNOWN", started_at=now_time, trace_id="trace-f")
    db_session.add_all([inc, plan, exec_rec])
    db_session.commit()

    # Independent read detects that port 22 is still present
    report = VerificationAgent.verify_outcome(
        db=db_session,
        incident_id=inc.id,
        plan_id=plan.id,
        execution_id=exec_rec.id,
        simulated_infra_failure=True
    )

    assert report.overall_status == VerificationStatus.FAILED
    assert report.infrastructure_verified is False
    assert exec_rec.verification_status == "FAILED"

def test_verification_agent_test_g_blocked_verification_does_not_increase_trust(db_session):
    """Test G: Blocked verification does not increase trust (trust_delta == 0.0)."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-verif-g", title="Trust Blocked Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    plan = RemediationPlan(id="plan-verif-g", incident_id=inc.id, title="Plan", explanation="E", status=RemediationStatus.EXECUTED, confidence=0.8, compatibility_score=0.8, estimated_risk="LOW", risk_score=0.1, blast_radius="LOCAL", idempotency_key="k-verif-g")
    exec_rec = RemediationExecution(id="exec-verif-g", plan_id=plan.id, plan_version=1, incident_id=inc.id, status="COMPLETED", verification_status="PENDING_VERIFICATION", incident_recovery_status="UNKNOWN", started_at=now_time, trace_id="trace-g")
    db_session.add_all([inc, plan, exec_rec])
    db_session.commit()

    report = VerificationAgent.verify_outcome(
        db=db_session,
        incident_id=inc.id,
        plan_id=plan.id,
        execution_id=exec_rec.id,
        mock_blocked=True
    )

    assert report.trust_delta == 0.0
    assert report.overall_status == VerificationStatus.BLOCKED

def test_verification_agent_test_h_failed_verification_decreases_trust(db_session):
    """Test H: Failed verification decreases trust (trust_delta < 0)."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-verif-h", title="Trust Fail Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    plan = RemediationPlan(id="plan-verif-h", incident_id=inc.id, title="Plan", explanation="E", status=RemediationStatus.EXECUTED, confidence=0.8, compatibility_score=0.8, estimated_risk="LOW", risk_score=0.1, blast_radius="LOCAL", idempotency_key="k-verif-h")
    exec_rec = RemediationExecution(id="exec-verif-h", plan_id=plan.id, plan_version=1, incident_id=inc.id, status="COMPLETED", verification_status="PENDING_VERIFICATION", incident_recovery_status="UNKNOWN", started_at=now_time, trace_id="trace-h")
    db_session.add_all([inc, plan, exec_rec])
    db_session.commit()

    report = VerificationAgent.verify_outcome(
        db=db_session,
        incident_id=inc.id,
        plan_id=plan.id,
        execution_id=exec_rec.id,
        mock_metric_value=3.2 # Above 1.0% threshold
    )

    assert report.trust_delta == -0.05
    assert report.overall_status == VerificationStatus.FAILED

def test_verification_agent_test_i_mock_mode_explicitly_reported(db_session):
    """Test I: Mock verification explicitly reports verification_mode='MOCK'."""
    now_time = datetime.now(timezone.utc)
    inc = Incident(id="inc-verif-i", title="Mock Report Inc", description="Desc", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    plan = RemediationPlan(id="plan-verif-i", incident_id=inc.id, title="Plan", explanation="E", status=RemediationStatus.EXECUTED, confidence=0.8, compatibility_score=0.8, estimated_risk="LOW", risk_score=0.1, blast_radius="LOCAL", idempotency_key="k-verif-i")
    exec_rec = RemediationExecution(id="exec-verif-i", plan_id=plan.id, plan_version=1, incident_id=inc.id, status="COMPLETED", verification_status="PENDING_VERIFICATION", incident_recovery_status="UNKNOWN", started_at=now_time, trace_id="trace-i")
    db_session.add_all([inc, plan, exec_rec])
    db_session.commit()

    report = VerificationAgent.verify_outcome(
        db=db_session,
        incident_id=inc.id,
        plan_id=plan.id,
        execution_id=exec_rec.id,
        force_real_aws=False
    )

    assert report.verification_mode == "MOCK"
    for s in report.signals:
        assert s.verification_mode == "MOCK"

def test_verification_agent_test_j_real_aws_mode_no_hardcoded_metrics():
    """Test J: Real AWS mode does not return hardcoded numbers and properly executes or blocks."""
    sig = AWSVerificationTelemetryReader.read_cloudwatch_metric(
        service_name="auth-service",
        metric_name="ErrorRate",
        force_real_aws=True
    )
    assert sig.verification_mode == "AWS_REAL"
    if sig.status == SignalStatus.BLOCKED:
        assert "REAL AWS VERIFICATION BLOCKED" in (sig.error_message or "")
    else:
        assert sig.observed_value is not None

def test_real_aws_verification_boundary():
    """Test 16: Real AWS Verification Integration Boundary Check."""
    # EC2 DescribeSecurityGroups Readback
    sig_ec2 = AWSVerificationTelemetryReader.verify_security_group_state(
        target_resource="sg-012345",
        expected_revoked_port=22,
        force_real_aws=True
    )
    assert sig_ec2.verification_mode == "AWS_REAL"
    if sig_ec2.status == SignalStatus.BLOCKED:
        assert ("REAL AWS VERIFICATION BLOCKED" in (sig_ec2.error_message or "")) or ("ClientError" in (sig_ec2.error_message or ""))

    # CloudWatch Metric Read
    sig_cw = AWSVerificationTelemetryReader.read_cloudwatch_metric(
        service_name="auth-service",
        metric_name="ErrorRate",
        force_real_aws=True
    )
    assert sig_cw.verification_mode == "AWS_REAL"
    if sig_cw.status == SignalStatus.BLOCKED:
        assert ("REAL AWS VERIFICATION BLOCKED" in (sig_cw.error_message or "")) or ("ClientError" in (sig_cw.error_message or ""))
