import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import InstitutionalMemoryVector, MemoryRegressionRecord, MemoryFeedback
from app.schemas.ghost_replay import MemoryRegression

class MemoryRegressionDetector:
    """
    Memory Regression Detector for GhostOps Stage 8.
    Detects 5 regression types and score drops <= -0.15.
    Feeds back to Stage 7 consolidation/review queue without silent memory deletion.
    """

    @classmethod
    def evaluate_memory_regressions(
        cls,
        db: Session,
        replay_id: str,
        memory_id: str,
        historical_score: float,
        observed_score: float,
        regression_type: str = "REMEDIATION_REGRESSION",
        explanation: str = "Memory remediation compatibility degraded under infrastructure version drift."
    ) -> Optional[MemoryRegressionRecord]:
        score_delta = round(observed_score - historical_score, 4)

        # Trigger regression if observed score < 0.70 or score drop <= -0.15
        is_regression = (observed_score < 0.70) or (score_delta <= -0.15)
        if not is_regression:
            return None

        severity = "CRITICAL" if observed_score < 0.50 else "HIGH" if score_delta <= -0.20 else "MEDIUM"

        reg_rec = MemoryRegressionRecord(
            id=f"reg-{uuid.uuid4().hex[:10]}",
            replay_id=replay_id,
            memory_id=memory_id,
            regression_type=regression_type,
            previous_confidence=historical_score,
            observed_confidence=observed_score,
            score_delta=score_delta,
            explanation=explanation,
            severity=severity,
            status="DETECTED"
        )
        db.add(reg_rec)

        # Record negative feedback entry in Stage 7 feedback table
        mem = db.get(InstitutionalMemoryVector, memory_id)
        if mem:
            fb = MemoryFeedback(
                id=f"fb-reg-{uuid.uuid4().hex[:10]}",
                memory_id=memory_id,
                incident_id="replay-validation",
                applicability=max(0.0, observed_score),
                used_for_investigation=True,
                used_for_remediation=True,
                remediation_result="REGRESSION_DETECTED",
                verification_result="FAILED",
                evidence_refs=[f"replay-{replay_id}"],
                confidence_delta=score_delta
            )
            db.add(fb)

        db.commit()
        return reg_rec
