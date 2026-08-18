from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Incident, RemediationPlan, PlanStep, InfrastructureSnapshot
from app.agents.graph import OrchestratorGraph
from app.agents.base import AgentState
from app.agents.specialists.planner import RemediationPlannerAgent
from app.services.governance.safety_engine import RemediationSafetyEngine
from app.schemas.remediation_governance import (
    RemediationPlanResponse,
    ValidationStatusResponse,
    ApprovalDecisionPayload,
    RejectionPayload,
    PlanStepPayload,
    ApprovalGate,
    RiskAssessment,
    SafetyCheckResult,
    RollbackAction,
    VerificationCheck
)
from ghostops_shared import RemediationStatus
from app.core.logging import logger

router = APIRouter()

def build_plan_response(plan: RemediationPlan) -> RemediationPlanResponse:
    step_payloads: List[PlanStepPayload] = []
    for s in plan.steps:
        rollback_data = s.rollback_parameters if s.rollback_parameters else None
        rb_action = RollbackAction(**rollback_data) if rollback_data and "action_type" in rollback_data else None

        step_payloads.append(PlanStepPayload(
            step_order=s.step_order,
            action_type=s.action_type,
            target_resource_arn=s.target_resource_arn,
            parameters=s.parameters or {},
            reason=plan.explanation,
            evidence_refs=plan.evidence_refs or [],
            risk_level=plan.estimated_risk,
            requires_approval=plan.requires_human_approval,
            idempotency_key=f"step-key-{plan.id}-{s.step_order}",
            preconditions=[f"Incident '{plan.incident_id}' active"],
            expected_effect="Target resource state restored.",
            failure_conditions=["API operation timeout"],
            rollback_action=rb_action,
            verification_requirements=[VerificationCheck(**v) for v in (plan.verification_plan or [])] if plan.verification_plan else [],
            status=s.status
        ))

    gate = ApprovalGate(**plan.approval_gate) if plan.approval_gate else ApprovalGate(
        approval_id=f"appv-{plan.id[:8]}",
        plan_id=plan.id,
        required=plan.requires_human_approval,
        requested_at=plan.created_at.isoformat() if plan.created_at else "",
        expires_at=plan.expires_at.isoformat() if plan.expires_at else ""
    )

    safety_list = [SafetyCheckResult(**c) for c in (plan.safety_checks or [])]
    rollback_list = [RollbackAction(**r) for r in (plan.rollback_plan or [])]
    verification_list = [VerificationCheck(**v) for v in (plan.verification_plan or [])]

    risk_info = RiskAssessment(
        risk_level=plan.estimated_risk,
        risk_score=plan.risk_score,
        blast_radius=plan.blast_radius,
        factors=[f"Action type risk: {plan.estimated_risk}", f"Blast radius: {plan.blast_radius}"]
    )

    return RemediationPlanResponse(
        plan_id=plan.id,
        incident_id=plan.incident_id,
        investigation_run_id=plan.investigation_run_id or "run-default",
        version=plan.version,
        title=plan.title,
        summary=plan.explanation,
        status=plan.status,
        root_cause_hypothesis_id=plan.root_cause_hypothesis_id or "H1",
        confidence=plan.confidence,
        compatibility_score=plan.compatibility_score,
        compatibility_classification=plan.compatibility_classification,
        risk=risk_info,
        steps=step_payloads,
        approval_gate=gate,
        safety_checks=safety_list,
        rollback_plan=rollback_list,
        verification_plan=verification_list,
        evidence_refs=plan.evidence_refs or [],
        historical_precedent_refs=plan.historical_precedent_refs or [],
        created_at=plan.created_at.isoformat() if plan.created_at else "",
        expires_at=plan.expires_at.isoformat() if plan.expires_at else ""
    )

@router.post("/incidents/{incident_id}/plans", response_model=RemediationPlanResponse, status_code=status.HTTP_201_CREATED)
def generate_remediation_plan(
    incident_id: str,
    db: Session = Depends(get_db)
):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

    state = AgentState(incident_id=incident.id, severity=incident.severity, target_resource_id=incident.target_resource_id)
    state.raw_events.append({"service": incident.service or "auth-service", "region": incident.region or "us-east-1", "title": incident.title})

    graph = OrchestratorGraph()
    inv_state = graph.run_investigation_graph(state, db)

    inv_response = {
        "run_id": inv_state.run_id,
        "confidence": inv_state.confidence,
        "selected_hypothesis": inv_state.hypotheses[0] if inv_state.hypotheses else None,
        "remediation_applicability": inv_state.remediation_applicability or {}
    }

    db_plan = RemediationPlannerAgent.generate_plan(db, incident, inv_response)
    return build_plan_response(db_plan)

@router.post("/plans/{plan_id}/validate", response_model=ValidationStatusResponse)
def validate_plan_safety(
    plan_id: str,
    db: Session = Depends(get_db)
):
    plan = db.get(RemediationPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found.")

    snap = db.scalars(
        select(InfrastructureSnapshot).where(InfrastructureSnapshot.incident_id == plan.incident_id)
    ).first()
    inv_snap = {
        "service_version": snap.service_version if snap else "v4.2.0",
        "db_version": snap.db_version if snap else "CockroachDB v23.2.3"
    } if snap else {}

    passed, risk_info, checks = RemediationSafetyEngine.evaluate_plan_safety(db, plan, inv_snap)

    plan.safety_checks = [c.model_dump() for c in checks]
    flag_modified(plan, "safety_checks")
    db.commit()

    drift_detected = any("drift" in c.check_name for c in checks if not c.passed)
    conflict_detected = any("conflict" in c.check_name for c in checks if not c.passed)
    expired = any("expiration" in c.check_name for c in checks if not c.passed)

    return ValidationStatusResponse(
        plan_id=plan.id,
        valid=passed,
        status="VALID" if passed else "BLOCKED",
        safety_checks=checks,
        drift_detected=drift_detected,
        conflict_detected=conflict_detected,
        expired=expired,
        message="Safety validation passed." if passed else "Safety engine validation checks failed."
    )

@router.post("/plans/{plan_id}/approve", response_model=RemediationPlanResponse)
def approve_remediation_plan(
    plan_id: str,
    payload: ApprovalDecisionPayload = ApprovalDecisionPayload(),
    db: Session = Depends(get_db)
):
    plan = db.get(RemediationPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found.")

    if plan.status in [RemediationStatus.APPROVED, RemediationStatus.READY_FOR_EXECUTION]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan is already approved.")

    now_time = datetime.now(timezone.utc)
    if plan.expires_at:
        exp_time = plan.expires_at.replace(tzinfo=timezone.utc) if plan.expires_at.tzinfo is None else plan.expires_at
        if now_time > exp_time:
            plan.status = RemediationStatus.REJECTED
            plan.rejection_reason = "Plan expired prior to approval."
            db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan has expired and cannot be approved.")

    # High-Risk Confirmation Text Enforcement
    if plan.estimated_risk in ["HIGH_RISK", "CRITICAL"]:
        expected_text = plan.approval_gate.get("confirmation_text", f"CONFIRM REVOKE INGRESS SG-012345")
        if not payload.confirmation_text or payload.confirmation_text.strip().upper() != expected_text.strip().upper():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"High-risk plan requires explicit confirmation text matching '{expected_text}'."
            )

    passed, _, checks = RemediationSafetyEngine.evaluate_plan_safety(db, plan)
    if not passed:
        plan.status = RemediationStatus.REJECTED
        plan.rejection_reason = "Safety checks failed during final approval validation."
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Safety checks failed during approval.")

    gate = dict(plan.approval_gate or {})
    gate["status"] = "APPROVED"
    gate["approved_at"] = now_time.isoformat()
    gate["approved_by"] = payload.approved_by
    gate["confirmation_text"] = payload.confirmation_text

    plan.approval_gate = gate
    flag_modified(plan, "approval_gate")

    plan.approved_by = payload.approved_by
    plan.approved_at = now_time
    plan.status = RemediationStatus.READY_FOR_EXECUTION
    db.commit()

    logger.info(f"[GovernanceAPI] Plan '{plan.id}' approved by '{payload.approved_by}'. Advanced to READY_FOR_EXECUTION.")
    return build_plan_response(plan)

@router.post("/plans/{plan_id}/reject", response_model=RemediationPlanResponse)
def reject_remediation_plan(
    plan_id: str,
    payload: RejectionPayload,
    db: Session = Depends(get_db)
):
    plan = db.get(RemediationPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found.")

    now_time = datetime.now(timezone.utc)
    gate = dict(plan.approval_gate or {})
    gate["status"] = "REJECTED"
    gate["rejection_reason"] = payload.rejection_reason

    plan.approval_gate = gate
    flag_modified(plan, "approval_gate")

    plan.rejection_reason = payload.rejection_reason
    plan.status = RemediationStatus.REJECTED
    db.commit()

    logger.info(f"[GovernanceAPI] Plan '{plan.id}' rejected by '{payload.rejected_by}'. Reason: {payload.rejection_reason}")
    return build_plan_response(plan)

@router.get("/plans/{plan_id}", response_model=RemediationPlanResponse)
def get_remediation_plan_detail(
    plan_id: str,
    db: Session = Depends(get_db)
):
    plan = db.get(RemediationPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found.")
    return build_plan_response(plan)

@router.get("/plans", response_model=List[RemediationPlanResponse])
def list_remediation_plans(
    db: Session = Depends(get_db)
):
    stmt = select(RemediationPlan).order_by(RemediationPlan.created_at.desc())
    plans = db.scalars(stmt).all()
    return [build_plan_response(p) for p in plans]
