from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from app.db.models.sentinel import SentinelAlert, SentinelEvent
from app.schemas.sentinel import SentinelPolicy

class AlertDeduplicationEngine:
    """
    Alert Deduplication & Storm Protection Engine for GhostOps Stage 9.
    Implements sliding-window deduplication and alert suppression using deduplication keys.
    """

    @classmethod
    def process_alert_deduplication(
        cls,
        db: Session,
        alert_candidate: SentinelAlert,
        policy: SentinelPolicy
    ) -> Tuple[bool, SentinelAlert, str]:
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=policy.dedup_window_seconds)

        # Query existing active alert with matching deduplication key within window
        existing_alert = db.query(SentinelAlert).filter(
            SentinelAlert.deduplication_key == alert_candidate.deduplication_key,
            SentinelAlert.last_seen_at >= cutoff_time
        ).first()

        if existing_alert:
            existing_alert.occurrence_count += 1
            existing_alert.suppressed_count += 1
            existing_alert.last_seen_at = datetime.now(timezone.utc)
            alert_candidate.status = "SUPPRESSED"
            db.commit()
            return True, alert_candidate, f"Suppressed duplicate alert matching key '{alert_candidate.deduplication_key}' within {policy.dedup_window_seconds}s window."

        # Insert new open alert
        db_alert = SentinelAlert(
            alert_id=alert_candidate.alert_id,
            sentinel_id=alert_candidate.sentinel_id,
            event_id=alert_candidate.event_id,
            fingerprint=alert_candidate.fingerprint,
            resource_id=alert_candidate.resource_id,
            severity=alert_candidate.severity,
            anomaly_score=alert_candidate.anomaly_score,
            confidence=alert_candidate.confidence,
            status="OPEN",
            deduplication_key=alert_candidate.deduplication_key,
            correlation_key=alert_candidate.correlation_key,
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
            occurrence_count=1,
            suppressed_count=0
        )
        db.add(db_alert)
        db.commit()
        return False, alert_candidate, "New unique alert created."
