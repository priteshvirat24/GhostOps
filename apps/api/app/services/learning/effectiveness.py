from app.db.models import RemediationOutcome
from app.schemas.learning_memory import OutcomeClassification

class EffectivenessEvaluator:
    """
    Deterministic Effectiveness Evaluator for GhostOps Stage 7.
    Calculates structured effectiveness score (0.0 to 1.0) using transparent component weights.
    """

    RECOVERY_WEIGHT = 0.40
    EXECUTION_WEIGHT = 0.25
    VERIFICATION_WEIGHT = 0.15
    ROLLBACK_WEIGHT = 0.10
    EVIDENCE_WEIGHT = 0.10

    @classmethod
    def evaluate_effectiveness(cls, outcome: RemediationOutcome) -> float:
        # 1. Recovery Component (0.40)
        rec_score = 1.0 if outcome.incident_recovery_status == "RECOVERED" else 0.0

        # 2. Execution Component (0.25)
        exec_score = 1.0 if outcome.execution_status == "COMPLETED" else 0.5 if outcome.executed_steps_count > 0 else 0.0

        # 3. Verification Component (0.15)
        verif_score = 1.0 if outcome.verification_status == "VERIFIED" else 0.0

        # 4. Rollback Component (0.10)
        if not outcome.rollback_performed:
            rb_score = 1.0
        else:
            rb_score = 1.0 if outcome.rollback_successful else 0.0

        # 5. Evidence Component (0.10)
        ev_score = 1.0 if len(outcome.evidence_refs or []) > 0 else 0.0

        # Calculate weighted raw score
        raw_score = (
            (rec_score * cls.RECOVERY_WEIGHT) +
            (exec_score * cls.EXECUTION_WEIGHT) +
            (verif_score * cls.VERIFICATION_WEIGHT) +
            (rb_score * cls.ROLLBACK_WEIGHT) +
            (ev_score * cls.EVIDENCE_WEIGHT)
        )

        # Failure Penalties
        penalty = 0.0
        if outcome.outcome_classification == OutcomeClassification.ROLLBACK_FAILED:
            penalty += 0.20
        elif outcome.outcome_classification == OutcomeClassification.COMPLETED_BUT_INCIDENT_PERSISTS:
            penalty += 0.15

        final_score = max(0.0, min(1.0, raw_score - penalty))
        return round(final_score, 4)
