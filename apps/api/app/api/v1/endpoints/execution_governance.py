from typing import List, Union
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import RemediationPlan, RemediationExecution, ExecutionStepRecord, ExecutionEventRecord, PlanStep
from app.schemas.remediation_execution import (
    ExecutionRequestPayload,
    DryRunResponse,
    ExecutionDetailResponse,
    ExecutionStepDetail,
    ExecutionEventPayload,
    ExecutionStatus,
    StepExecutionStatus
)
from app.services.execution.precheck_engine import ExecutionPrecheckEngine
from app.services.execution.saga_engine import RemediationSagaEngine
from app.services.execution.lock_manager import ExecutionLockManager
from app.services.execution.action_executors import TypedActionExecutors
from app.core.logging import logger
from ghostops_shared import RemediationStatus

router = APIRouter()

def build_execution_detail_response(exec_rec: RemediationExecution) -> ExecutionDetailResponse:
    step_details: List[ExecutionStepDetail] = []
    for s in exec_rec.steps_detail:
        step_details.append(ExecutionStepDetail(
            execution_step_id=s.id,
            step_order=s.step_order,
            action_type=s.action_type,
            target_resource=s.target_resource,
            execution_mode=getattr(s, "execution_mode", "MOCK"),
            status=s.status,
            idempotency_key=s.idempotency_key,
            started_at=s.started_at.isoformat() if s.started_at else None,
            completed_at=s.completed_at.isoformat() if s.completed_at else None,
            attempt_count=s.attempt_count,
            request_id=s.request_id,
            result_summary=s.result_summary,
            failure_reason=s.failure_reason,
            pre_state=TypedActionExecutors.redact_secrets(s.pre_state or {}),
            post_state=TypedActionExecutors.redact_secrets(s.post_state or {}),
            compensation_status=s.compensation_status,
            verification_status=s.verification_status
        ))

    event_details: List[ExecutionEventPayload] = []
    for e in exec_rec.events:
        event_details.append(ExecutionEventPayload(
            event_id=e.id,
            execution_id=e.execution_id,
            step_id=e.step_id,
            event_type=e.event_type,
            timestamp=e.created_at.isoformat() if e.created_at else "",
            actor=e.actor,
            request_id=e.request_id,
            summary=e.summary,
            metadata=TypedActionExecutors.redact_secrets(e.metadata_json or {}),
            severity=e.severity
        ))

    return ExecutionDetailResponse(
        execution_id=exec_rec.id,
        plan_id=exec_rec.plan_id,
        plan_version=exec_rec.plan_version,
        incident_id=exec_rec.incident_id,
        status=exec_rec.status,
        execution_mode=getattr(exec_rec, "execution_mode", "MOCK"),
        started_at=exec_rec.started_at.isoformat() if exec_rec.started_at else "",
        completed_at=exec_rec.completed_at.isoformat() if exec_rec.completed_at else None,
        failure_reason=exec_rec.failure_reason,
        termination_reason=exec_rec.termination_reason,
        current_step=exec_rec.current_step,
        executed_steps=exec_rec.executed_steps,
        compensated_steps=exec_rec.compensated_steps,
        verification_status=exec_rec.verification_status,
        incident_recovery_status=exec_rec.incident_recovery_status,
        lock_id=exec_rec.lock_id,
        executor=exec_rec.executor,
        trace_id=exec_rec.trace_id,
        steps_detail=step_details,
        events=event_details,
        created_at=exec_rec.created_at.isoformat() if exec_rec.created_at else "",
        updated_at=exec_rec.updated_at.isoformat() if exec_rec.updated_at else ""
    )

@router.post("/plans/{plan_id}/execute", response_model=Union[ExecutionDetailResponse, DryRunResponse], status_code=status.HTTP_200_OK)
def execute_remediation_plan(
    plan_id: str,
    payload: ExecutionRequestPayload = ExecutionRequestPayload(),
    db: Session = Depends(get_db)
):
    """
    Triggers governed saga execution or dry-run simulation for an approved plan.
    Does NOT mutate infrastructure in dry-run mode or if prechecks fail.
    """
    plan = db.get(RemediationPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found.")

    # 1. Run Pre-Execution Safety Checks
    passed, prechecks = ExecutionPrecheckEngine.run_prechecks(db, plan)

    # 2. Dry-Run Mode Simulation
    if payload.dry_run:
        step_sims = []
        for s in plan.steps:
            step_sims.append({
                "step_order": s.step_order,
                "action_type": s.action_type,
                "target_resource": s.target_resource_arn,
                "parameters": s.parameters,
                "reason": plan.explanation
            })

        return DryRunResponse(
            dry_run=True,
            would_execute=passed,
            plan_id=plan.id,
            plan_version=plan.version,
            steps=step_sims,
            expected_pre_state={"connection_pool_max": 50, "security_group_ingress_rules": [{"port": 22}]},
            expected_post_state={"connection_pool_max": 150, "security_group_ingress_rules": []},
            rollback_plan=plan.rollback_plan or [],
            verification_plan=plan.verification_plan or [],
            risk={"risk_level": plan.estimated_risk, "risk_score": plan.risk_score, "blast_radius": plan.blast_radius},
            blocking_conditions=[c.message for c in prechecks if not c.passed]
        )

    if not passed:
        blocking_msg = "; ".join([c.message for c in prechecks if not c.passed])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Pre-execution safety prechecks failed: {blocking_msg}")

    # 3. Trigger Governed Saga Execution
    exec_rec = RemediationSagaEngine.execute_plan_saga(
        db,
        plan,
        requested_by=payload.requested_by,
        force_real_aws=payload.force_real_aws
    )
    return build_execution_detail_response(exec_rec)

@router.get("/executions/{execution_id}", response_model=ExecutionDetailResponse)
def get_execution_detail(
    execution_id: str,
    db: Session = Depends(get_db)
):
    exec_rec = db.get(RemediationExecution, execution_id)
    if not exec_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{execution_id}' not found.")
    return build_execution_detail_response(exec_rec)

@router.post("/executions/{execution_id}/cancel", response_model=ExecutionDetailResponse)
def cancel_remediation_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    exec_rec = db.get(RemediationExecution, execution_id)
    if not exec_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{execution_id}' not found.")

    if exec_rec.status in [ExecutionStatus.COMPLETED, ExecutionStatus.ROLLED_BACK, ExecutionStatus.CANCELLED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Execution is already terminal and cannot be cancelled.")

    exec_rec.status = ExecutionStatus.CANCELLED
    exec_rec.termination_reason = "CANCELLED_BY_USER"
    exec_rec.completed_at = datetime.now(timezone.utc)

    ExecutionLockManager.release_lock(db, exec_rec.lock_id)
    db.commit()

    RemediationSagaEngine.log_event(db, execution_id, "EXECUTION_CANCELLED", "Execution safely cancelled by user request.")
    return build_execution_detail_response(exec_rec)

@router.post("/executions/{execution_id}/rollback", response_model=ExecutionDetailResponse)
def trigger_manual_rollback(
    execution_id: str,
    db: Session = Depends(get_db)
):
    exec_rec = db.get(RemediationExecution, execution_id)
    if not exec_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{execution_id}' not found.")

    plan = db.get(RemediationPlan, exec_rec.plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated remediation plan not found.")

    exec_rec.status = ExecutionStatus.ROLLING_BACK
    db.commit()

    # Re-acquire lock for rollback
    ExecutionLockManager.acquire_lock(db, plan.incident_id, plan.id, exec_rec.id)

    RemediationSagaEngine.log_event(db, execution_id, "MANUAL_ROLLBACK_TRIGGERED", "Manual rollback saga initiated by operator.")

    # Perform compensation for executed steps
    for s in reversed(exec_rec.steps_detail):
        if s.status in [StepExecutionStatus.SUCCEEDED, StepExecutionStatus.VERIFIED]:
            s.status = StepExecutionStatus.COMPENSATING
            db.commit()

            plan_step_obj = db.get(PlanStep, s.plan_step_id)
            rb_params = plan_step_obj.rollback_parameters if plan_step_obj and plan_step_obj.rollback_parameters else {"action_type": s.action_type, "parameters": {}}

            comp_ok, _, _, c_summary, _ = TypedActionExecutors.compensate_action(s.action_type, s.target_resource, rb_params)
            if comp_ok:
                s.status = StepExecutionStatus.COMPENSATED
                s.compensation_status = "COMPENSATED"
                exec_rec.compensated_steps += 1
                db.commit()
                RemediationSagaEngine.log_event(db, execution_id, "COMPENSATION_SUCCEEDED", c_summary, step_id=s.id)
            else:
                s.status = StepExecutionStatus.COMPENSATION_FAILED
                s.compensation_status = "COMPENSATION_FAILED"
                db.commit()
                RemediationSagaEngine.log_event(db, execution_id, "COMPENSATION_FAILED", c_summary, step_id=s.id, severity="CRITICAL")

    exec_rec.status = ExecutionStatus.ROLLED_BACK
    exec_rec.termination_reason = "MANUAL_ROLLBACK_COMPLETED"
    exec_rec.completed_at = datetime.now(timezone.utc)

    ExecutionLockManager.release_lock(db, exec_rec.lock_id)
    db.commit()

    return build_execution_detail_response(exec_rec)

@router.get("/plans/{plan_id}/executions", response_model=List[ExecutionDetailResponse])
def list_plan_executions(
    plan_id: str,
    db: Session = Depends(get_db)
):
    stmt = select(RemediationExecution).where(RemediationExecution.plan_id == plan_id).order_by(RemediationExecution.started_at.desc())
    execs = db.scalars(stmt).all()
    return [build_execution_detail_response(e) for e in execs]
