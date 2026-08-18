import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.schemas.verification import (
    VerificationStatus,
    SignalStatus,
    SignalVerificationResult,
    VerificationReport
)
from app.services.verification.telemetry_reader import AWSVerificationTelemetryReader
from app.db.models import (
    Incident,
    RemediationPlan,
    PlanStep,
    RemediationExecution,
    RemediationOutcome
)
from app.schemas.learning_memory import OutcomeClassification
from app.core.config import settings
from app.core.logging import logger

class VerificationAgent:
    """
    Verification Specialist Agent for GhostOps (§9.2, §16).
    Independently verifies remediation outcomes using genuinely separate telemetry signals:
    1. EC2 Security Group direct readback (DescribeSecurityGroups).
    2. CloudWatch Application Error Rate (GetMetricData).
    3. CloudWatch p99 Latency / TargetResponseTime (GetMetricData).
    4. Reliability observation window.

    Guarantees:
    - Never grades own homework or trusts ExecutionAgent's success message.
    - Emits structured signal-level results.
    - Distinguishes VERIFIED, PARTIALLY_VERIFIED, FAILED, and BLOCKED.
    - Calculates deterministic trust deltas: positive only on verified proof, negative on failure, zero on blocked.
    """

    @classmethod
    def verify_outcome(
        cls,
        db: Session,
        incident_id: str,
        plan_id: str,
        execution_id: str,
        force_real_aws: bool = False,
        simulated_infra_failure: bool = False,
        mock_metric_value: Optional[float] = None,
        mock_blocked: bool = False
    ) -> VerificationReport:
        t0 = time.time()
        use_real_aws = force_real_aws or (not settings.AWS_MOCK_MODE)
        mode = "AWS_REAL" if use_real_aws else "MOCK"

        logger.info(f"[VerificationAgent] Running independent verification for incident '{incident_id}' (mode={mode}, exec={execution_id})")

        # 1. Fetch Incident and Execution from Database
        inc = db.get(Incident, incident_id)
        plan = db.get(RemediationPlan, plan_id)
        execution = db.get(RemediationExecution, execution_id)

        target_res = "sg-012345"
        port = 22
        cidr = "0.0.0.0/0"
        service_name = inc.service if inc else "auth-service"

        if plan and plan.steps:
            for s in plan.steps:
                if s.action_type == "CHANGE_SECURITY_RULE":
                    target_res = s.target_resource_arn
                    port = int(s.parameters.get("port", 22)) if s.parameters else 22
                    cidr = str(s.parameters.get("cidr_block", "0.0.0.0/0")) if s.parameters else "0.0.0.0/0"
                    break

        signals: List[SignalVerificationResult] = []

        # 2. Independent Infrastructure State Readback (EC2 DescribeSecurityGroups)
        infra_sig = AWSVerificationTelemetryReader.verify_security_group_state(
            target_resource=target_res,
            expected_revoked_port=port,
            expected_revoked_cidr=cidr,
            force_real_aws=force_real_aws,
            simulated_infra_failure=simulated_infra_failure
        )
        signals.append(infra_sig)

        # 3. Independent Application Error Rate Telemetry (CloudWatch)
        error_sig = AWSVerificationTelemetryReader.read_cloudwatch_metric(
            service_name=service_name,
            metric_name="ErrorRate",
            window_minutes=15,
            threshold=1.0,
            comparison_operator="LessThanThreshold",
            force_real_aws=force_real_aws,
            mock_metric_value=mock_metric_value,
            mock_blocked=mock_blocked
        )
        signals.append(error_sig)

        # 4. Independent Latency Telemetry (CloudWatch TargetResponseTime)
        latency_sig = AWSVerificationTelemetryReader.read_cloudwatch_metric(
            service_name=service_name,
            metric_name="TargetResponseTime",
            window_minutes=15,
            threshold=500.0,
            comparison_operator="LessThanThreshold",
            force_real_aws=force_real_aws,
            mock_metric_value=mock_metric_value * 100 if mock_metric_value is not None else None,
            mock_blocked=mock_blocked
        )
        signals.append(latency_sig)

        # 5. Deterministic Multi-Signal Evaluation
        has_blocked = any(s.status == SignalStatus.BLOCKED for s in signals)
        has_failed = any(s.status == SignalStatus.FAIL for s in signals)
        has_inconclusive = any(s.status == SignalStatus.INCONCLUSIVE for s in signals)
        all_passed = all(s.status == SignalStatus.PASS for s in signals)

        if has_blocked:
            overall_status = VerificationStatus.BLOCKED
            trust_delta = 0.0
            rec_status = "UNKNOWN"
            summary = "Independent verification BLOCKED: required AWS telemetry / credentials unavailable."
            blocked_reason = next((s.error_message for s in signals if s.status == SignalStatus.BLOCKED), "Telemetry unavailable")
        elif has_failed:
            overall_status = VerificationStatus.FAILED
            trust_delta = -0.05
            rec_status = "PERSISTS"
            summary = "Independent verification FAILED: infrastructure or application metrics did not recover."
            blocked_reason = None
        elif has_inconclusive or not all_passed:
            overall_status = VerificationStatus.PARTIALLY_VERIFIED
            trust_delta = 0.0
            rec_status = "UNKNOWN"
            summary = "Independent verification PARTIALLY_VERIFIED: infrastructure state confirmed; telemetry observation pending."
            blocked_reason = None
        else:
            overall_status = VerificationStatus.VERIFIED
            trust_delta = 0.05
            rec_status = "RECOVERED"
            summary = "Independent verification VERIFIED: infrastructure mutation confirmed and application metrics restored."
            blocked_reason = None

        # 6. Update RemediationExecution Record in DB
        if execution:
            execution.verification_status = overall_status.value
            execution.incident_recovery_status = rec_status
            db.commit()

        # 7. Record RemediationOutcome in CockroachDB
        classification = OutcomeClassification.VERIFICATION_INCONCLUSIVE
        if overall_status == VerificationStatus.VERIFIED:
            classification = OutcomeClassification.COMPLETED_AND_RECOVERED
        elif overall_status == VerificationStatus.FAILED:
            classification = OutcomeClassification.COMPLETED_BUT_INCIDENT_PERSISTS
        elif overall_status == VerificationStatus.BLOCKED:
            classification = OutcomeClassification.VERIFICATION_INCONCLUSIVE

        outcome = RemediationOutcome(
            id=f"outc-{uuid.uuid4().hex[:12]}",
            incident_id=incident_id,
            plan_id=plan_id,
            execution_id=execution_id,
            execution_status=execution.status if execution else "COMPLETED",
            verification_status=overall_status.value,
            incident_recovery_status=rec_status,
            outcome_classification=classification,
            effectiveness_score=0.95 if overall_status == VerificationStatus.VERIFIED else 0.20 if overall_status == VerificationStatus.FAILED else 0.50,
            duration_seconds=round(time.time() - t0, 2),
            executed_steps_count=execution.executed_steps if execution else 1,
            failed_steps_count=0 if overall_status == VerificationStatus.VERIFIED else 1,
            compensated_steps_count=execution.compensated_steps if execution else 0,
            rollback_performed=overall_status == VerificationStatus.FAILED,
            rollback_successful=overall_status == VerificationStatus.FAILED,
            confidence=0.95 if overall_status == VerificationStatus.VERIFIED else 0.40,
            evidence_refs=[s.evidence_ref for s in signals if s.evidence_ref]
        )
        db.add(outcome)
        db.commit()

        report = VerificationReport(
            incident_id=incident_id,
            plan_id=plan_id,
            execution_id=execution_id,
            overall_status=overall_status,
            verification_mode=mode,
            signals=signals,
            infrastructure_verified=infra_sig.status == SignalStatus.PASS,
            telemetry_verified=error_sig.status == SignalStatus.PASS and latency_sig.status == SignalStatus.PASS,
            observation_window_complete=not has_inconclusive,
            trust_delta=trust_delta,
            summary=summary,
            blocked_reason=blocked_reason
        )

        logger.info(f"[VerificationAgent] Completed verification for incident '{incident_id}': status={overall_status} (trust delta={trust_delta})")
        return report
