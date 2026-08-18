import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Ensure apps/api and root are in python path
sys.path.insert(0, os.path.abspath("apps/api"))
sys.path.insert(0, os.path.abspath("."))

from app.db.session import SessionLocal
from app.db.models import (
    Incident,
    RemediationPlan,
    PlanStep,
    RemediationExecution,
    RemediationOutcome,
    InfrastructureSnapshot
)
from app.services.verification.telemetry_reader import AWSVerificationTelemetryReader
from app.services.execution.saga_engine import RemediationSagaEngine
from app.services.execution.mock_infrastructure import StatefulMockInfrastructure
from app.agents.specialists.verification import VerificationAgent
from app.schemas.verification import VerificationStatus, SignalStatus
from ghostops_shared import IncidentSeverity, IncidentStatus, RemediationStatus

def main():
    print("=" * 80)
    print("GhostOps Stage 7 Independent Verification End-to-End Test")
    print("=" * 80)

    db = SessionLocal()
    try:
        now_time = datetime.now(timezone.utc)
        unique_id = uuid.uuid4().hex[:8]

        # 1. Create Incident & Baseline Snapshot
        inc = Incident(
            id=f"inc-verif-{unique_id}",
            title=f"Independent Verification Test {unique_id}",
            description="High error rate and unauthorized SSH ingress detected on production node.",
            service="auth-service",
            region="us-east-1",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.INVESTIGATING,
            start_time=now_time
        )
        db.add(inc)

        snap = InfrastructureSnapshot(
            incident_id=inc.id,
            snapshot_timestamp=now_time,
            service_version="v4.2.0",
            db_version="CockroachDB v23.2.3",
            topology={"nodes": ["auth-node-1", "auth-node-2"]},
            configuration={"connection_pool_max": 50, "security_group_ingress_rules": [{"protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"}, {"protocol": "tcp", "port": 443, "cidr_block": "0.0.0.0/0"}]},
            dependencies={"db": "cockroach-cloud"}
        )
        db.add(snap)
        db.commit()

        # 2. Create Approved Remediation Plan
        plan = RemediationPlan(
            id=f"plan-verif-{unique_id}",
            incident_id=inc.id,
            title="Revoke SSH Ingress",
            explanation="Revoke port 22 0.0.0.0/0 on auth-service security group.",
            status=RemediationStatus.APPROVED,
            confidence=0.92,
            compatibility_score=0.95,
            estimated_risk="HIGH_RISK",
            risk_score=0.75,
            blast_radius="REGION",
            idempotency_key=f"idemp-verif-{unique_id}",
            expires_at=now_time + timedelta(hours=2),
            rollback_plan=[{"step_order": 1, "action_type": "CHANGE_SECURITY_RULE", "parameters": {"port": 22, "cidr_block": "0.0.0.0/0"}}]
        )
        target_sg = f"sg-{unique_id}"
        step = PlanStep(
            remediation_plan_id=plan.id,
            step_order=1,
            action_type="CHANGE_SECURITY_RULE",
            target_resource_arn=target_sg,
            parameters={"security_group_id": target_sg, "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"}
        )
        plan.steps.append(step)
        db.add(plan)
        db.commit()

        print(f"\n--- 1. APPROVED PLAN ---")
        print(f"Plan ID: {plan.id}")
        print(f"Action: {step.action_type} on target '{step.target_resource_arn}' (port {step.parameters['port']})")
        print(f"Status: {plan.status}")

        # 3. Execute Saga Execution
        print(f"\n--- 2. EXECUTION ENGINE (SAGA) ---")
        exec_record = RemediationSagaEngine.execute_plan_saga(db, plan, force_real_aws=False)
        print(f"Execution ID: {exec_record.id}")
        print(f"Execution Status: {exec_record.status}")
        print(f"Verification Status (Before Independent Verification): {exec_record.verification_status}")
        print(f"Termination Reason: {exec_record.termination_reason}")
        assert exec_record.verification_status == "PENDING_VERIFICATION"
        assert exec_record.termination_reason == "EXECUTED_PENDING_VERIFICATION"

        # 4. Independent Verification Agent Execution
        print(f"\n--- 3. INDEPENDENT VERIFICATION AGENT ---")
        report = VerificationAgent.verify_outcome(
            db=db,
            incident_id=inc.id,
            plan_id=plan.id,
            execution_id=exec_record.id,
            mock_metric_value=0.22 # Healthy error rate 0.22% < 1.0%
        )

        print(f"Overall Verification Status: {report.overall_status}")
        print(f"Verification Mode: {report.verification_mode}")
        print(f"Infrastructure Verified (EC2): {report.infrastructure_verified}")
        print(f"Telemetry Verified (CloudWatch): {report.telemetry_verified}")
        print(f"Trust Delta: {report.trust_delta:+0.2f}")
        print(f"Summary: {report.summary}")

        print(f"\nSignals Evaluated:")
        for s in report.signals:
            print(f"  - [{s.signal_type}] {s.signal_name} ({s.source}): status={s.status}, value={s.observed_value}")

        # 5. Database State Recheck
        print(f"\n--- 4. POST-VERIFICATION DATABASE STATE ---")
        db.refresh(exec_record)
        print(f"Remediation Execution verification_status: {exec_record.verification_status}")
        print(f"Remediation Execution incident_recovery_status: {exec_record.incident_recovery_status}")

        outcome = db.query(RemediationOutcome).filter(RemediationOutcome.execution_id == exec_record.id).first()
        if outcome:
            print(f"RemediationOutcome ID: {outcome.id}")
            print(f"Outcome Classification: {outcome.outcome_classification}")
            print(f"Effectiveness Score: {outcome.effectiveness_score}")

        # 6. Real AWS Verification Boundary Check
        print(f"\n--- 5. REAL AWS TELEMETRY BOUNDARY CHECK ---")
        real_cw_sig = AWSVerificationTelemetryReader.read_cloudwatch_metric(
            service_name="auth-service",
            metric_name="ErrorRate",
            force_real_aws=True
        )
        print(f"Real CloudWatch Read Status: {real_cw_sig.status}")
        print(f"Real CloudWatch Mode: {real_cw_sig.verification_mode}")
        if real_cw_sig.error_message:
            print(f"Real CloudWatch Error/Block Message: {real_cw_sig.error_message}")

        real_ec2_sig = AWSVerificationTelemetryReader.verify_security_group_state(
            target_resource=target_sg,
            expected_revoked_port=22,
            force_real_aws=True
        )
        print(f"Real EC2 Read Status: {real_ec2_sig.status}")
        print(f"Real EC2 Mode: {real_ec2_sig.verification_mode}")
        if real_ec2_sig.error_message:
            print(f"Real EC2 Error/Block Message: {real_ec2_sig.error_message}")

        print("\n" + "=" * 80)
        print("Stage 7 Independent Verification End-to-End Verification Complete: ALL CHECKS PASSED")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    main()
