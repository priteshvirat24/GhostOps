from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import RemediationPlan
from app.schemas.remediation import RemediationPlanResponse, PlanApprovalRequest

router = APIRouter()

@router.get("", response_model=List[RemediationPlanResponse])
def list_plans(db: Session = Depends(get_db)):
    stmt = select(RemediationPlan).order_by(RemediationPlan.created_at.desc())
    return list(db.scalars(stmt).all())

@router.post("/{plan_id}/approve", response_model=dict)
def approve_plan(plan_id: str, request: PlanApprovalRequest, db: Session = Depends(get_db)):
    plan = db.get(RemediationPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Remediation plan not found")
    
    if request.approved:
        plan.status = "APPROVED"
        plan.approved_by = request.approved_by
    else:
        plan.status = "REJECTED"
        plan.rejection_reason = request.rejection_reason

    db.commit()
    return {"id": plan.id, "status": plan.status}
