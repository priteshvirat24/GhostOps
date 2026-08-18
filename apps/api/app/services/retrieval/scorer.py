from typing import List, Dict, Any, Optional, Tuple
from app.db.models import Incident, OperationalActionHistory
from app.services.retrieval.staleness import StalenessCalculator
from app.core.config import settings

class HybridScorer:
    """
    Hybrid scoring component combining structured, vector, outcome, trust, and staleness signals.
    Uses configurable weights defined in app.core.config.settings.
    """

    @staticmethod
    def compute_outcome_score(actions: List[OperationalActionHistory]) -> Tuple[float, str]:
        if not actions:
            return 0.5, "UNKNOWN"

        has_success = any(a.result == "SUCCESS" for a in actions)
        has_failed_only = all(a.result == "FAILED" for a in actions)

        if has_success:
            return 1.0, "SUCCESSFUL_REMEDIATION"
        elif has_failed_only:
            return 0.0, "ALL_ATTEMPTS_FAILED"
        return 0.5, "PARTIAL_REMEDIATION"

    @staticmethod
    def calculate_hybrid_score(
        structured_score: float,
        semantic_score: float,
        outcome_score: float,
        trust_score: float,
        staleness_penalty: float
    ) -> float:
        w_struct = settings.STRUCTURED_WEIGHT
        w_vec = settings.VECTOR_WEIGHT
        w_outcome = settings.OUTCOME_WEIGHT
        w_trust = settings.TRUST_WEIGHT
        w_stale = settings.STALENESS_WEIGHT

        raw_score = (
            (w_struct * structured_score) +
            (w_vec * semantic_score) +
            (w_outcome * outcome_score) +
            (w_trust * trust_score) -
            (w_stale * staleness_penalty)
        )

        return round(max(0.0, min(1.0, raw_score)), 4)
