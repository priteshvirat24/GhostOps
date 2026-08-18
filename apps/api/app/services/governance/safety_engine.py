import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.db.models import RemediationPlan, PlanStep
from app.schemas.remediation_governance import SafetyCheckResult, RiskAssessment
from app.services.governance.action_catalog import ActionCatalog
from app.services.governance.drift_detector import DriftDetector
from ghostops_shared import RemediationStatus

class RemediationSafetyEngine:
    """
    Deterministic Safety & Governance Engine for GhostOps Stage 5.
    Evaluates risk score, blast radius, preconditions, rollback & verification completeness,
    expiration, drift detection, and concurrent remediation locking.
    """

    @classmethod
    def evaluate_plan_safety(
        cls,
        db: Session,
        plan: RemediationPlan,
        investigation_snapshot: Dict[str, Any] = None
    ) -> Tuple[bool, RiskAssessment, List[SafetyCheckResult]]:
        safety_checks: List[SafetyCheckResult] = []
        now_time = datetime.now(timezone.utc)

        # 1. Action Catalog & Parameter Integrity Check
        catalog_passed = True
        highest_action_risk = "LOW_RISK"
        highest_blast_radius = "LOCAL"

        for step in plan.steps:
            errors = ActionCatalog.validate_action(step.action_type, step.target_resource_arn, step.parameters or {})
            if errors:
                catalog_passed = False
                for err in errors:
                    safety_checks.append(SafetyCheckResult(
                        passed=False, check_name=f"action_catalog_{step.step_order}", severity="HIGH", message=err, blocking=True
                    ))

            defn = ActionCatalog.get_action_definition(step.action_type)
            if defn:
                if defn.default_safety_level in ["CRITICAL", "HIGH_RISK"]:
                    highest_action_risk = defn.default_safety_level
                elif defn.default_safety_level == "MEDIUM_RISK" and highest_action_risk == "LOW_RISK":
                    highest_action_risk = "MEDIUM_RISK"

                if defn.default_blast_radius in ["GLOBAL", "REGION"]:
                    highest_blast_radius = defn.default_blast_radius
                elif defn.default_blast_radius == "CLUSTER" and highest_blast_radius == "LOCAL":
                    highest_blast_radius = "CLUSTER"

        if catalog_passed:
            safety_checks.append(SafetyCheckResult(
                passed=True, check_name="action_catalog_validation", severity="LOW", message="All plan action types and parameters comply with authorized action catalog.", blocking=False
            ))

        # 2. Deterministic Risk Scoring
        base_risk_map = {"READ_ONLY": 0.05, "LOW_RISK": 0.15, "MEDIUM_RISK": 0.40, "HIGH_RISK": 0.70, "CRITICAL": 0.90}
        blast_map = {"LOCAL": 0.05, "SERVICE": 0.10, "CLUSTER": 0.20, "REGION": 0.30, "GLOBAL": 0.40}

        base_val = base_risk_map.get(highest_action_risk, 0.25)
        blast_val = blast_map.get(highest_blast_radius, 0.10)
        uncertainty_penalty = (1.0 - plan.confidence) * 0.25
        incompatibility_penalty = (1.0 - plan.compatibility_score) * 0.25

        has_rollback = len(plan.rollback_plan or []) > 0
        rollback_bonus = 0.15 if has_rollback else 0.0

        raw_risk = base_val + blast_val + uncertainty_penalty + incompatibility_penalty - rollback_bonus
        final_risk_score = round(max(0.05, min(0.99, raw_risk)), 4)

        if final_risk_score >= 0.75:
            final_risk_level = "HIGH_RISK"
        elif final_risk_score >= 0.45:
            final_risk_level = "MEDIUM_RISK"
        else:
            final_risk_level = "LOW_RISK"

        risk_assessment = RiskAssessment(
            risk_level=final_risk_level,
            risk_score=final_risk_score,
            blast_radius=highest_blast_radius,
            factors=[
                f"Action type risk level: {highest_action_risk}",
                f"Blast radius scope: {highest_blast_radius}",
                f"Investigation confidence: {plan.confidence}",
                f"Temporal compatibility: {plan.compatibility_score}",
                f"Rollback plan defined: {has_rollback}"
            ]
        )

        # 3. Minimum Confidence Threshold Check (Must be >= 0.60)
        conf_passed = plan.confidence >= 0.60
        safety_checks.append(SafetyCheckResult(
            passed=conf_passed,
            check_name="confidence_threshold",
            severity="HIGH",
            message=f"Investigation confidence ({plan.confidence}) meets minimum 0.60 threshold." if conf_passed else f"Confidence ({plan.confidence}) below 0.60 threshold.",
            blocking=not conf_passed
        ))

        # 4. Rollback & Verification Plan Completeness Check
        has_verification = len(plan.verification_plan or []) > 0
        safety_checks.append(SafetyCheckResult(
            passed=has_rollback,
            check_name="rollback_plan_completeness",
            severity="HIGH" if highest_action_risk in ["HIGH_RISK", "CRITICAL"] else "MEDIUM",
            message="Typed rollback plan defined for all mutating steps." if has_rollback else "Missing rollback plan for mutating remediation actions.",
            blocking=highest_action_risk in ["HIGH_RISK", "CRITICAL"] and not has_rollback
        ))

        safety_checks.append(SafetyCheckResult(
            passed=has_verification,
            check_name="verification_plan_completeness",
            severity="MEDIUM",
            message="Independent verification conditions defined." if has_verification else "Missing independent verification metrics.",
            blocking=False
        ))

        # 5. Plan Expiration Check
        if plan.expires_at:
            exp_time = plan.expires_at.replace(tzinfo=timezone.utc) if plan.expires_at.tzinfo is None else plan.expires_at
            is_expired = now_time > exp_time
            safety_checks.append(SafetyCheckResult(
                passed=not is_expired,
                check_name="plan_expiration_check",
                severity="HIGH",
                message=f"Plan is active (expires at {exp_time.isoformat()})." if not is_expired else "Plan has expired and requires regeneration.",
                blocking=is_expired
            ))

        # 6. Infrastructure Drift Detection
        if investigation_snapshot:
            drift_detected, drift_factors = DriftDetector.detect_drift(db, plan.incident_id, investigation_snapshot)
            safety_checks.append(SafetyCheckResult(
                passed=not drift_detected,
                check_name="infrastructure_drift_check",
                severity="HIGH",
                message="No infrastructure baseline drift detected." if not drift_detected else f"PLAN_BLOCKED_BY_DRIFT: {'; '.join(drift_factors)}",
                blocking=drift_detected
            ))

        # 7. Concurrent Remediation Conflict Lock
        conflicting_plan = db.scalars(
            select(RemediationPlan)
            .where(
                and_(
                    RemediationPlan.incident_id == plan.incident_id,
                    RemediationPlan.id != plan.id,
                    RemediationPlan.status.in_([RemediationStatus.READY_FOR_EXECUTION, RemediationStatus.EXECUTING])
                )
            )
        ).first()

        has_conflict = conflicting_plan is not None
        safety_checks.append(SafetyCheckResult(
            passed=not has_conflict,
            check_name="concurrent_remediation_conflict_check",
            severity="CRITICAL",
            message="No conflicting concurrent remediation active." if not has_conflict else f"PLAN_BLOCKED_BY_CONCURRENT_REMEDIATION: Plan '{conflicting_plan.id}' is currently active.",
            blocking=has_conflict
        ))

        overall_passed = all(c.passed for c in safety_checks if c.blocking)
        return overall_passed, risk_assessment, safety_checks
