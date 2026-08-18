import uuid
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import select

from app.db.models import (
    RemediationPlan,
    RemediationExecution,
    ExecutionStepRecord,
    ExecutionEventRecord,
    OperationalActionHistory,
    PlanStep
)
from app.schemas.remediation_execution import ExecutionStatus, StepExecutionStatus, LockStatus
from app.services.execution.state_machine import ExecutionStateMachine
from app.services.execution.precheck_engine import ExecutionPrecheckEngine
from app.services.execution.lock_manager import ExecutionLockManager
from app.services.execution.action_executors import TypedActionExecutors
from app.services.execution.verification_engine import RemediationVerificationEngine
from app.schemas.remediation_governance import VerificationCheck
from app.core.config import settings
from ghostops_shared import RemediationStatus
from app.core.logging import logger

class RemediationSagaEngine:
    """
    Saga Execution & Compensation Engine for GhostOps Stage 6.
    Executes approved remediation plans as governed sagas with idempotency, step state tracking,
    timeout reconciliation, reverse-dependency compensation on failure, and audit trace logging.
    """

    @classmethod
    def execute_plan_saga(
        cls,
        db: Session,
        plan: RemediationPlan,
        requested_by: str = "DevOpsLead",
        simulated_step_failure: bool = False,
        simulated_rollback_failure: bool = False,
        simulated_incident_recovery: bool = True,
        simulated_timeout: bool = False,
        force_real_aws: bool = False
    ) -> RemediationExecution:
        now_time = datetime.now(timezone.utc)
        exec_id = f"exec-{uuid.uuid4().hex[:12]}"
        trace_id = f"trace-exec-{uuid.uuid4().hex[:8]}"
        initial_mode = "AWS_REAL" if (force_real_aws or not settings.AWS_MOCK_MODE) else "MOCK"

        logger.info(f"[SagaEngine] Starting saga execution '{exec_id}' for plan '{plan.id}' (mode={initial_mode}, version {plan.version})")

        # 1. Create Initial RemediationExecution Record in PENDING status
        db_exec = RemediationExecution(
            id=exec_id,
            plan_id=plan.id,
            plan_version=plan.version,
            incident_id=plan.incident_id,
            status=ExecutionStatus.PENDING,
            execution_mode=initial_mode,
            started_at=now_time,
            executor=requested_by,
            trace_id=trace_id,
            verification_status="PENDING_VERIFICATION",
            incident_recovery_status="UNKNOWN"
        )
        db.add(db_exec)
        db.commit()

        cls.log_event(db, exec_id, "EXECUTION_CREATED", f"Saga execution initialized for plan '{plan.id}' (mode={initial_mode})", actor=requested_by)

        # 2. Run Prechecks (Approval, Drift, Expiration, Safety Engine)
        db_exec.status = ExecutionStatus.PRECHECKING
        db.commit()
        cls.log_event(db, exec_id, "PRECHECK_STARTED", "Re-validating plan approval, safety conditions, and infrastructure baseline.")

        prechecks_passed, precheck_results = ExecutionPrecheckEngine.run_prechecks(db, plan)
        if not prechecks_passed:
            drift_failed = any("drift" in c.check_name for c in precheck_results if not c.passed)
            if drift_failed:
                plan.status = RemediationStatus.REJECTED
                plan.rejection_reason = "REQUIRES_REVALIDATION: Baseline infrastructure drift detected prior to execution."
                db.commit()

            db_exec.status = ExecutionStatus.BLOCKED
            db_exec.termination_reason = "BLOCKED_BY_DRIFT" if drift_failed else "BLOCKED_BY_PRECHECKS"
            db_exec.failure_reason = "; ".join([c.message for c in precheck_results if not c.passed])
            db_exec.completed_at = datetime.now(timezone.utc)
            db.commit()
            cls.log_event(db, exec_id, "PRECHECK_FAILED", f"Pre-execution safety checks failed: {db_exec.failure_reason}", severity="ERROR")
            return db_exec

        cls.log_event(db, exec_id, "PRECHECK_PASSED", "All pre-execution safety conditions satisfied.")

        # 3. Acquire Distributed Execution Lock
        lock_scope = plan.incident_id
        lock_acquired, lock_rec, lock_msg = ExecutionLockManager.acquire_lock(db, lock_scope, plan.id, exec_id)
        if not lock_acquired:
            db_exec.status = ExecutionStatus.BLOCKED
            db_exec.termination_reason = "BLOCKED_BY_LOCK"
            db_exec.failure_reason = lock_msg
            db_exec.completed_at = datetime.now(timezone.utc)
            db.commit()
            cls.log_event(db, exec_id, "LOCK_CONVENTION_BLOCKED", lock_msg, severity="ERROR")
            return db_exec

        db_exec.lock_id = lock_rec.id
        db_exec.status = ExecutionStatus.READY
        db.commit()
        cls.log_event(db, exec_id, "LOCK_ACQUIRED", f"Execution lock '{lock_rec.id}' acquired.")

        # 4. Advance to EXECUTING
        db_exec.status = ExecutionStatus.EXECUTING
        db.commit()

        completed_step_records: List[ExecutionStepRecord] = []
        saga_failed = False
        failure_step_order = 0

        for step in plan.steps:
            db_exec.current_step = step.step_order
            db.commit()

            step_idempotency_key = f"step-key-{plan.id}-{step.step_order}-{step.action_type}-{step.target_resource_arn}"

            # Check Idempotency protection before executing AWS call (§9, §15)
            existing_action = db.scalars(
                select(OperationalActionHistory).where(
                    OperationalActionHistory.idempotency_key == step_idempotency_key,
                    OperationalActionHistory.result == "SUCCESS"
                )
            ).first()

            step_rec = ExecutionStepRecord(
                id=f"exec-step-{uuid.uuid4().hex[:8]}",
                execution_id=exec_id,
                plan_step_id=step.id,
                step_order=step.step_order,
                action_type=step.action_type,
                target_resource=step.target_resource_arn,
                execution_mode=initial_mode,
                status=StepExecutionStatus.EXECUTING,
                idempotency_key=step_idempotency_key,
                started_at=datetime.now(timezone.utc),
                attempt_count=1
            )
            db.add(step_rec)
            db.commit()

            cls.log_event(db, exec_id, "STEP_STARTED", f"Step {step.step_order} started: '{step.action_type}' on '{step.target_resource_arn}' (mode={initial_mode})", step_id=step_rec.id)

            if existing_action:
                # Idempotent replay: return existing success without re-invoking AWS
                logger.info(f"[SagaEngine] Idempotent key '{step_idempotency_key}' already succeeded. Reusing prior execution result.")
                step_rec.status = StepExecutionStatus.SUCCEEDED
                step_rec.verification_status = "PENDING_VERIFICATION"
                step_rec.result_summary = f"[IDEMPOTENT_REPLAY] Step previously executed successfully (Action ID: {existing_action.id})."
                step_rec.completed_at = datetime.now(timezone.utc)
                db_exec.executed_steps += 1
                db.commit()

                completed_step_records.append(step_rec)
                cls.log_event(db, exec_id, "IDEMPOTENT_STEP_REPLAY", step_rec.result_summary, step_id=step_rec.id)
                continue

            should_fail = simulated_step_failure and step.step_order == len(plan.steps)
            should_timeout = simulated_timeout and step.step_order == 1

            # Execute via Governed AWS Action Executor
            success, pre_st, post_st, req_id, summary, exec_mode = TypedActionExecutors.execute_action(
                action_type=step.action_type,
                target_resource=step.target_resource_arn,
                parameters=step.parameters or {},
                idempotency_key=step_idempotency_key,
                simulated_failure=should_fail,
                simulated_timeout=should_timeout,
                force_real_aws=force_real_aws
            )

            step_rec.execution_mode = exec_mode
            db_exec.execution_mode = exec_mode

            if should_timeout and not success:
                cls.log_event(db, exec_id, "ACTION_TIMEOUT", "AWS API request timed out. Executing state reconciliation...", step_id=step_rec.id, severity="WARNING")
                reconciled, recon_msg = TypedActionExecutors.reconcile_timeout_state(step.action_type, step.target_resource_arn, step.parameters or {})
                if reconciled:
                    success = True
                    summary = recon_msg
                    cls.log_event(db, exec_id, "TIMEOUT_RECONCILED", recon_msg, step_id=step_rec.id)

            step_rec.request_id = req_id
            step_rec.pre_state = pre_st
            step_rec.post_state = post_st
            step_rec.result_summary = summary

            if success:
                step_rec.status = StepExecutionStatus.SUCCEEDED
                step_rec.verification_status = "PENDING_VERIFICATION"
                step_rec.completed_at = datetime.now(timezone.utc)
                db_exec.executed_steps += 1
                db.commit()

                completed_step_records.append(step_rec)
                cls.log_event(db, exec_id, "ACTION_SUCCEEDED", summary, step_id=step_rec.id)

                act_hist = OperationalActionHistory(
                    incident_id=plan.incident_id,
                    saga_id=exec_id,
                    actor=requested_by,
                    agent="RemediationSagaEngine",
                    command=step.action_type,
                    tool="AWSActionExecutor",
                    target=step.target_resource_arn,
                    execution_mode=exec_mode,
                    risk_level=step.remediation_plan.estimated_risk if step.remediation_plan else "LOW",
                    reason=step.reason if hasattr(step, 'reason') else "Saga execution",
                    authorization=f"ApprovedPlan_v{plan.version}",
                    idempotency_key=step_idempotency_key,
                    result="SUCCESS"
                )
                db.add(act_hist)
                db.commit()
            else:
                saga_failed = True
                failure_step_order = step.step_order
                step_rec.status = StepExecutionStatus.FAILED
                step_rec.failure_reason = summary
                step_rec.completed_at = datetime.now(timezone.utc)
                db.commit()
                cls.log_event(db, exec_id, "ACTION_FAILED", summary, step_id=step_rec.id, severity="ERROR")

                act_hist_failed = OperationalActionHistory(
                    incident_id=plan.incident_id,
                    saga_id=exec_id,
                    actor=requested_by,
                    agent="RemediationSagaEngine",
                    command=step.action_type,
                    tool="AWSActionExecutor",
                    target=step.target_resource_arn,
                    execution_mode=exec_mode,
                    risk_level=step.remediation_plan.estimated_risk if step.remediation_plan else "LOW",
                    reason=step.reason if hasattr(step, 'reason') else "Saga execution",
                    authorization=f"ApprovedPlan_v{plan.version}",
                    idempotency_key=step_idempotency_key,
                    result="FAILED",
                    error_message=summary
                )
                db.add(act_hist_failed)
                db.commit()
                break

        # 5. Handle Saga Failure & Reverse-Dependency Compensation
        if saga_failed:
            db_exec.status = ExecutionStatus.FAILED
            db_exec.failure_reason = f"Step {failure_step_order} failed execution: {step_rec.failure_reason}"
            db.commit()

            cls.log_event(db, exec_id, "COMPENSATION_STARTED", "Saga execution failed. Initializing reverse-dependency compensation...", severity="WARNING")
            db_exec.status = ExecutionStatus.ROLLING_BACK
            db.commit()

            rollback_failed = False
            for step_rec in reversed(completed_step_records):
                step_rec.status = StepExecutionStatus.COMPENSATING
                db.commit()

                plan_step_obj = db.get(PlanStep, step_rec.plan_step_id)
                rb_params = plan_step_obj.rollback_parameters if plan_step_obj and plan_step_obj.rollback_parameters else {"action_type": step_rec.action_type, "parameters": {}}

                comp_ok, c_pre, c_post, c_summary, c_mode = TypedActionExecutors.compensate_action(
                    action_type=step_rec.action_type,
                    target_resource=step_rec.target_resource,
                    rollback_parameters=rb_params,
                    force_real_aws=force_real_aws
                )

                if simulated_rollback_failure:
                    comp_ok = False
                    c_summary = "Simulated compensation infrastructure failure."

                if comp_ok:
                    step_rec.status = StepExecutionStatus.COMPENSATED
                    step_rec.compensation_status = "COMPENSATED"
                    db_exec.compensated_steps += 1
                    db.commit()
                    cls.log_event(db, exec_id, "COMPENSATION_SUCCEEDED", c_summary, step_id=step_rec.id)
                else:
                    rollback_failed = True
                    step_rec.status = StepExecutionStatus.COMPENSATION_FAILED
                    step_rec.compensation_status = "COMPENSATION_FAILED"
                    db.commit()
                    cls.log_event(db, exec_id, "COMPENSATION_FAILED", c_summary, step_id=step_rec.id, severity="CRITICAL")

            if rollback_failed:
                db_exec.status = ExecutionStatus.ROLLBACK_FAILED
                db_exec.termination_reason = "ROLLBACK_FAILED"
                cls.log_event(db, exec_id, "ROLLBACK_FAILED", "Reverse compensation encountered failures. System in unrecovered state.", severity="CRITICAL")
            else:
                db_exec.status = ExecutionStatus.ROLLED_BACK
                db_exec.termination_reason = "ROLLED_BACK_SUCCESSFULLY"
                cls.log_event(db, exec_id, "ROLLBACK_COMPLETED", "All completed steps compensated in reverse dependency order.")

            db_exec.completed_at = datetime.now(timezone.utc)
            ExecutionLockManager.release_lock(db, db_exec.lock_id)
            db.commit()
            return db_exec

        # 6. Mark Executed Pending Independent Verification (§17)
        db_exec.status = ExecutionStatus.COMPLETED
        db_exec.termination_reason = "EXECUTED_PENDING_VERIFICATION"
        db_exec.verification_status = "PENDING_VERIFICATION"
        db_exec.incident_recovery_status = "UNKNOWN"
        db_exec.completed_at = datetime.now(timezone.utc)
        plan.status = RemediationStatus.EXECUTED
        db.commit()

        ExecutionLockManager.release_lock(db, db_exec.lock_id)
        db.commit()

        cls.log_event(db, exec_id, "EXECUTION_COMPLETED", f"Saga execution completed in mode '{db_exec.execution_mode}'. Pending independent verification.")
        logger.info(f"[SagaEngine] Completed execution '{exec_id}' in mode '{db_exec.execution_mode}' with status {db_exec.status}")
        return db_exec

    @classmethod
    def log_event(
        cls,
        db: Session,
        execution_id: str,
        event_type: str,
        summary: str,
        step_id: Optional[str] = None,
        actor: str = "GhostOps.SagaEngine",
        severity: str = "INFO",
        metadata: Dict[str, Any] = None
    ):
        clean_meta = TypedActionExecutors.redact_secrets(metadata or {})
        evt = ExecutionEventRecord(
            id=f"evt-{uuid.uuid4().hex[:10]}",
            execution_id=execution_id,
            step_id=step_id,
            event_type=event_type,
            actor=actor,
            summary=summary,
            metadata_json=clean_meta,
            severity=severity
        )
        db.add(evt)
        db.commit()
