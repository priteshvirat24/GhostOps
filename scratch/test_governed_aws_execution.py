import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Ensure python path includes apps/api
sys.path.insert(0, os.path.abspath("apps/api"))

from app.db.session import SessionLocal, get_db
from app.db.models import (
    Incident,
    InfrastructureSnapshot,
    RemediationPlan,
    PlanStep,
    RemediationExecution,
    ExecutionStepRecord,
    OperationalActionHistory
)
from app.services.execution.aws_executor import AWSActionExecutor
from app.services.execution.saga_engine import RemediationSagaEngine
from app.services.execution.action_executors import TypedActionExecutors
from app.services.execution.precheck_engine import ExecutionPrecheckEngine
from app.schemas.remediation_execution import ExecutionStatus, StepExecutionStatus
from ghostops_shared import IncidentSeverity, RemediationStatus

def main():
    print("=" * 80)
    print("GhostOps Stage 6 Governed AWS Execution Verification")
    print("=" * 80)

    db = SessionLocal()
    now_time = datetime.now(timezone.utc)

    try:
        # 1. Action Selection & Narrow Boundary Demonstration
        print("\n--- 1. SELECTED ACTION & AWS BOUNDARY ---")
        print("Selected Action: CHANGE_SECURITY_RULE (EC2 RevokeSecurityGroupIngress / AuthorizeSecurityGroupIngress)")
        print("Governed Executor: AWSActionExecutor (boto3 EC2 client boundary)")

        # 2. Test MOCK Execution Mode
        print("\n--- 2. DETERMINISTIC MOCK EXECUTION ---")
        mock_success, mock_pre, mock_post, req_id, mock_summary, mock_mode = AWSActionExecutor.execute_action(
            action_type="CHANGE_SECURITY_RULE",
            target_resource="arn:aws:ec2:us-east-1:123456789012:security-group/sg-0a1b2c3d4e5f",
            parameters={
                "security_group_id": "sg-0a1b2c3d4e5f",
                "protocol": "tcp",
                "port": 22,
                "cidr_block": "0.0.0.0/0",
                "secret_token": "super_secret_token_123"
            },
            idempotency_key=f"idemp-mock-{uuid.uuid4().hex[:6]}",
            force_real_aws=False
        )
        print(f"Mock Success: {mock_success}")
        print(f"Execution Mode: {mock_mode}")
        print(f"Request ID: {req_id}")
        print(f"Summary: {mock_summary}")
        print(f"Pre-State (Redacted): {mock_pre}")
        print(f"Post-State (Redacted): {mock_post}")
        assert mock_mode == "MOCK"
        assert "[MOCK]" in mock_summary

        # 3. Test REAL AWS Boundary
        print("\n--- 3. REAL AWS EXECUTION PATH ---")
        real_success, real_pre, real_post, real_req_id, real_summary, real_mode = AWSActionExecutor.execute_action(
            action_type="CHANGE_SECURITY_RULE",
            target_resource="arn:aws:ec2:us-east-1:123456789012:security-group/sg-0a1b2c3d4e5f",
            parameters={
                "security_group_id": "sg-0a1b2c3d4e5f",
                "protocol": "tcp",
                "port": 22,
                "cidr_block": "0.0.0.0/0"
            },
            idempotency_key=f"idemp-real-{uuid.uuid4().hex[:6]}",
            force_real_aws=True
        )
        print(f"Real Execution Success: {real_success}")
        print(f"Execution Mode: {real_mode}")
        print(f"Summary: {real_summary}")
        assert real_mode == "AWS_REAL"
        assert "SIMULATED_SUCCESS" not in real_summary

        # 4. Full Saga Execution with Prechecks, Idempotency & Audit Trace
        print("\n--- 4. FULL GOVERNED SAGA EXECUTION ---")
        inc = Incident(
            id=f"inc-e2e-{uuid.uuid4().hex[:8]}",
            title="SSH Ingress Security Violation",
            description="Unauthorized 0.0.0.0/0 SSH rule detected on auth cluster.",
            service="auth-service",
            region="us-east-1",
            severity=IncidentSeverity.HIGH,
            start_time=now_time
        )
        db.add(inc)
        db.commit()

        plan = RemediationPlan(
            id=f"plan-e2e-{uuid.uuid4().hex[:8]}",
            incident_id=inc.id,
            title="Revoke SSH Ingress on Security Group",
            explanation="Revoke unauthenticated port 22 access.",
            status=RemediationStatus.APPROVED,
            confidence=0.92,
            compatibility_score=0.95,
            estimated_risk="HIGH_RISK",
            risk_score=0.85,
            blast_radius="REGION",
            idempotency_key=f"plan-idemp-{uuid.uuid4().hex[:8]}",
            expires_at=now_time + timedelta(hours=24),
            rollback_plan=[{"action_type": "CHANGE_SECURITY_RULE", "reason": "Rollback"}],
            verification_plan=[{"check_id": "v1", "type": "CLOUDWATCH_METRIC", "target": "auth-service", "expected_condition": "CPU < 50%"}]
        )
        step = PlanStep(
            remediation_plan_id=plan.id,
            step_order=1,
            action_type="CHANGE_SECURITY_RULE",
            target_resource_arn="sg-0a1b2c3d4e5f",
            parameters={"security_group_id": "sg-0a1b2c3d4e5f", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"},
            rollback_parameters={"security_group_id": "sg-0a1b2c3d4e5f", "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0", "is_rollback": True}
        )
        plan.steps.append(step)
        db.add(plan)
        db.commit()

        # Execute Saga
        exec_record = RemediationSagaEngine.execute_plan_saga(db, plan, requested_by="SecOpsLead")
        print(f"Execution ID: {exec_record.id}")
        print(f"Execution Status: {exec_record.status}")
        print(f"Execution Mode: {exec_record.execution_mode}")
        print(f"Verification Status: {exec_record.verification_status}")
        print(f"Termination Reason: {exec_record.termination_reason}")
        print(f"Executed Steps: {exec_record.executed_steps}")
        print(f"Audit Events Logged: {len(exec_record.events)}")

        # 5. Test Idempotency Deduplication
        print("\n--- 5. IDEMPOTENCY DEDUPLICATION ---")
        exec_record_dup = RemediationSagaEngine.execute_plan_saga(db, plan, requested_by="SecOpsLead")
        print(f"Replay Execution ID: {exec_record_dup.id}")
        print(f"Replay Execution Status: {exec_record_dup.status}")
        print(f"Replay Step Status: {exec_record_dup.steps_detail[0].status}")
        print(f"Replay Summary: {exec_record_dup.steps_detail[0].result_summary}")
        assert "[IDEMPOTENT_REPLAY]" in exec_record_dup.steps_detail[0].result_summary

        # 6. Verify Operational Action Ledger
        actions = db.query(OperationalActionHistory).filter(OperationalActionHistory.incident_id == inc.id).all()
        print(f"\n--- 6. OPERATIONAL ACTION HISTORY ---")
        print(f"Total Actions in Ledger: {len(actions)}")
        for a in actions:
            print(f"  - Action [{a.command}] on [{a.target}]: result={a.result}, mode={a.execution_mode}, auth={a.authorization}")

        print("\nAll Stage 6 Governed AWS Execution Validations Completed Successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
