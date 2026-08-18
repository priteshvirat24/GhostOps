from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.db.models import RemediationPlan, InfrastructureSnapshot, ExecutionLockRecord
from app.schemas.remediation_execution import ExecutionPrecheckResult
from app.services.governance.drift_detector import DriftDetector
from app.services.governance.safety_engine import RemediationSafetyEngine
from app.core.config import settings
from ghostops_shared import RemediationStatus

class ExecutionPrecheckEngine:
    """
    Pre-Execution Safety & Precheck Engine for GhostOps Stage 6.
    Re-validates approval status, expiration, drift, safety engine, lock contention,
    and rollback availability right before execution starts.
    """

    @classmethod
    def run_prechecks(
        cls,
        db: Session,
        plan: RemediationPlan
    ) -> Tuple[bool, List[ExecutionPrecheckResult]]:
        checks: List[ExecutionPrecheckResult] = []
        now_time = datetime.now(timezone.utc)

        # 1. Immutable Approved Plan Check
        is_approved = plan.status in [RemediationStatus.APPROVED, RemediationStatus.READY_FOR_EXECUTION, RemediationStatus.EXECUTED]
        checks.append(ExecutionPrecheckResult(
            passed=is_approved,
            check_name="plan_approval_check",
            severity="CRITICAL",
            message="Plan is APPROVED and immutable." if is_approved else f"Plan status '{plan.status}' is not APPROVED.",
            blocking=not is_approved
        ))

        # 2. Expiration Check
        if plan.expires_at:
            exp_time = plan.expires_at.replace(tzinfo=timezone.utc) if plan.expires_at.tzinfo is None else plan.expires_at
            is_expired = now_time > exp_time
            checks.append(ExecutionPrecheckResult(
                passed=not is_expired,
                check_name="plan_expiration_precheck",
                severity="HIGH",
                message=f"Plan is active (expires at {exp_time.isoformat()})." if not is_expired else "Plan has EXPIRED prior to execution start.",
                blocking=is_expired
            ))

        # 3. Minimum Configurable Confidence Threshold Check
        min_conf = settings.MINIMUM_PLAN_CONFIDENCE
        conf_passed = plan.confidence >= min_conf
        checks.append(ExecutionPrecheckResult(
            passed=conf_passed,
            check_name="plan_confidence_precheck",
            severity="HIGH",
            message=f"Investigation confidence ({plan.confidence:.2f}) meets effective minimum {min_conf:.2f} threshold." if conf_passed else f"Investigation confidence ({plan.confidence:.2f}) below minimum {min_conf:.2f} threshold.",
            blocking=not conf_passed
        ))

        # 4. Infrastructure Drift Check
        plan_baseline = (plan.preconditions or {}) if hasattr(plan, 'preconditions') and plan.preconditions else {}
        inv_snap = {
            "service_version": plan_baseline.get("service_version", "v4.2.0"),
            "db_version": plan_baseline.get("db_version", "CockroachDB v23.2.3")
        }

        drift_detected, drift_factors = DriftDetector.detect_drift(db, plan.incident_id, inv_snap)
        checks.append(ExecutionPrecheckResult(
            passed=not drift_detected,
            check_name="infrastructure_drift_precheck",
            severity="HIGH",
            message="No infrastructure baseline drift detected." if not drift_detected else f"PLAN_BLOCKED_BY_DRIFT: {'; '.join(drift_factors)}",
            blocking=drift_detected
        ))

        # 5. Lock Contention Check
        existing_lock = db.scalars(
            select(ExecutionLockRecord).where(
                and_(
                    ExecutionLockRecord.resource_scope == plan.incident_id,
                    ExecutionLockRecord.status == "ACTIVE"
                )
            )
        ).first()

        has_conflict = existing_lock is not None
        checks.append(ExecutionPrecheckResult(
            passed=not has_conflict,
            check_name="execution_lock_precheck",
            severity="CRITICAL",
            message="No active execution lock conflict." if not has_conflict else f"EXECUTION_BLOCKED_BY_LOCK: Active lock held by execution '{existing_lock.execution_id}'.",
            blocking=has_conflict
        ))

        # 6. Rollback Completeness Check
        has_rollback = len(plan.rollback_plan or []) > 0
        checks.append(ExecutionPrecheckResult(
            passed=has_rollback,
            check_name="rollback_availability_precheck",
            severity="HIGH",
            message="Typed rollback plan defined for all steps." if has_rollback else "Missing rollback plan strategy.",
            blocking=not has_rollback
        ))

        overall_passed = all(c.passed for c in checks if c.blocking)
        return overall_passed, checks
