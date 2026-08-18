import uuid
from datetime import datetime, timezone
from typing import Tuple, Optional
from app.schemas.sentinel import SentinelEvent, SentinelAlert, SentinelPolicy

class AnomalyDetectionEngine:
    """
    Anomaly Detection Engine for GhostOps Stage 9.
    Evaluates telemetry event metrics, error rate spikes, and state shifts to calculate deterministic anomaly scores (0.0 to 1.0).
    """

    @classmethod
    def evaluate_event(
        cls,
        event: SentinelEvent,
        policy: SentinelPolicy
    ) -> Tuple[bool, Optional[SentinelAlert]]:
        # Compute anomaly score based on metric deviation and severity
        base_score = 0.50
        if event.deviation and event.baseline_value and event.baseline_value > 0:
            dev_ratio = abs(event.deviation) / event.baseline_value
            base_score += min(0.40, dev_ratio * 0.20)

        if event.severity in ["HIGH", "CRITICAL"]:
            base_score += 0.15
        elif event.severity == "MEDIUM":
            base_score += 0.05

        anomaly_score = min(1.0, round(base_score, 4))
        confidence = min(0.95, round(anomaly_score * 0.90, 4))

        is_anomaly = anomaly_score >= policy.anomaly_threshold

        if not is_anomaly:
            return False, None

        now_str = datetime.now(timezone.utc).isoformat()
        alert = SentinelAlert(
            alert_id=f"alt-{uuid.uuid4().hex[:10]}",
            sentinel_id=event.sentinel_id,
            event_id=event.event_id,
            fingerprint=event.fingerprint,
            resource_id=event.resource_id,
            severity=event.severity,
            anomaly_score=anomaly_score,
            confidence=confidence,
            status="OPEN",
            deduplication_key=event.deduplication_key,
            correlation_key=event.correlation_key,
            first_seen_at=now_str,
            last_seen_at=now_str,
            occurrence_count=1,
            suppressed_count=0,
            incident_id=event.incident_id
        )

        return True, alert
