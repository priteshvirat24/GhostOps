import uuid
import time
from datetime import datetime, timezone
from typing import Tuple, Dict, Any, List
from sqlalchemy.orm import Session

from app.db.models import RemediationExecution, RemediationPlan, RemediationOutcome
from app.schemas.learning_memory import OutcomeClassification

class RemediationOutcomeAnalyzer:
    """
    Post-Remediation Outcome Analyzer for GhostOps Stage 7.
    Analyzes actual Stage 6 execution and verification records to classify outcome.
    Does NOT infer recovery merely from execution status.
    """

    @classmethod
    def analyze_execution_outcome(
        cls,
        db: Session,
        execution: RemediationExecution
    ) -> RemediationOutcome:
        # Check if outcome record already exists for execution (Idempotency)
        existing_outcome = db.query(RemediationOutcome).filter(
            RemediationOutcome.execution_id == execution.id
        ).first()

        if existing_outcome:
            return existing_outcome

        exec_status = execution.status
        recovery_status = execution.incident_recovery_status
        verif_status = execution.verification_status

        executed_count = execution.executed_steps
        compensated_count = execution.compensated_steps

        rollback_perf = compensated_count > 0 or exec_status in ["ROLLING_BACK", "ROLLED_BACK", "ROLLBACK_FAILED"]
        rollback_succ = exec_status == "ROLLED_BACK"

        # Classify Outcome
        if exec_status == "COMPLETED" and recovery_status == "RECOVERED":
            classification = OutcomeClassification.COMPLETED_AND_RECOVERED
        elif exec_status in ["COMPLETED", "COMPLETED_WITH_WARNINGS"] and recovery_status == "PERSISTS":
            classification = OutcomeClassification.COMPLETED_BUT_INCIDENT_PERSISTS
        elif exec_status == "ROLLED_BACK" and recovery_status == "RECOVERED":
            classification = OutcomeClassification.ROLLED_BACK_AND_RECOVERED
        elif exec_status == "ROLLED_BACK" and recovery_status != "RECOVERED":
            classification = OutcomeClassification.ROLLED_BACK_BUT_INCIDENT_PERSISTS
        elif exec_status == "ROLLBACK_FAILED":
            classification = OutcomeClassification.ROLLBACK_FAILED
        elif exec_status in ["FAILED", "CANCELLED", "BLOCKED"]:
            classification = OutcomeClassification.EXECUTION_FAILED
        else:
            classification = OutcomeClassification.VERIFICATION_INCONCLUSIVE

        # Collect evidence references
        ev_refs: List[str] = [f"exec-{execution.id}"]
        for s in execution.steps_detail:
            if s.request_id:
                ev_refs.append(s.request_id)

        # Calculate duration
        duration = 0.0
        if execution.started_at and execution.completed_at:
            t1 = execution.started_at.replace(tzinfo=timezone.utc) if execution.started_at.tzinfo is None else execution.started_at
            t2 = execution.completed_at.replace(tzinfo=timezone.utc) if execution.completed_at.tzinfo is None else execution.completed_at
            duration = (t2 - t1).total_seconds()

        outcome = RemediationOutcome(
            id=f"outc-{uuid.uuid4().hex[:12]}",
            incident_id=execution.incident_id,
            plan_id=execution.plan_id,
            execution_id=execution.id,
            execution_status=exec_status,
            verification_status=verif_status,
            incident_recovery_status=recovery_status,
            outcome_classification=classification,
            effectiveness_score=0.0,  # Will be calculated by EffectivenessEvaluator
            duration_seconds=max(1.0, duration),
            executed_steps_count=executed_count,
            failed_steps_count=1 if exec_status in ["FAILED", "ROLLING_BACK", "ROLLBACK_FAILED"] else 0,
            compensated_steps_count=compensated_count,
            rollback_performed=rollback_perf,
            rollback_successful=rollback_succ,
            before_state={"status": "INCIDENT_ACTIVE"},
            after_state={"status": recovery_status},
            recovery_metrics={"incident_recovery": recovery_status, "duration_seconds": duration},
            evidence_refs=ev_refs,
            confidence=0.90 if classification == OutcomeClassification.COMPLETED_AND_RECOVERED else 0.70
        )

        db.add(outcome)
        db.commit()
        return outcome
