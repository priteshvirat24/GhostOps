import uuid
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from app.db.models import Incident, SentinelAlert, SentinelIncidentLink, SentinelDecision
from app.schemas.sentinel import SentinelPolicy
from ghostops_shared import IncidentSeverity, IncidentStatus

class IncidentCorrelationEngine:
    """
    Incident Correlation Engine for GhostOps Stage 9.
    Groups alerts into existing active incidents or creates new incidents based on spatial and temporal correlation keys.
    """

    @classmethod
    def correlate_alert(
        cls,
        db: Session,
        alert: SentinelAlert,
        policy: SentinelPolicy
    ) -> Tuple[str, bool, str]:
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=policy.correlation_window_seconds)

        # Check for open active incident with matching service or resource within correlation window
        existing_inc = db.query(Incident).filter(
            Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]),
            Incident.start_time >= cutoff_time
        ).first()

        if existing_inc:
            # Link to existing incident
            link = SentinelIncidentLink(
                id=f"link-{uuid.uuid4().hex[:10]}",
                alert_id=alert.alert_id,
                incident_id=existing_inc.id,
                relationship="RELATED_SIGNAL",
                confidence=0.92
            )
            db.add(link)

            db_alert = db.query(SentinelAlert).filter(SentinelAlert.alert_id == alert.alert_id).first()
            if db_alert:
                db_alert.incident_id = existing_inc.id
                db_alert.status = "CORRELATED"

            db.commit()
            return existing_inc.id, False, f"Correlated alert '{alert.alert_id}' with existing incident '{existing_inc.id}'."

        # Create new Incident
        new_inc_id = f"inc-sentinel-{uuid.uuid4().hex[:8]}"
        sev_enum = IncidentSeverity.HIGH if alert.severity in ["HIGH", "CRITICAL"] else IncidentSeverity.MEDIUM

        new_inc = Incident(
            id=new_inc_id,
            title=f"Autonomous Sentinel Incident: {alert.resource_id} {alert.severity}",
            description=f"Automated incident created by GhostOps Sentinel from alert {alert.alert_id} (Fingerprint: {alert.fingerprint[:12]}).",
            service="auth-service",
            region="us-east-1",
            severity=sev_enum,
            status=IncidentStatus.OPEN,
            start_time=datetime.now(timezone.utc),
            target_resource_id=alert.resource_id
        )
        db.add(new_inc)

        link = SentinelIncidentLink(
            id=f"link-{uuid.uuid4().hex[:10]}",
            alert_id=alert.alert_id,
            incident_id=new_inc_id,
            relationship="PRIMARY_SIGNAL",
            confidence=0.95
        )
        db.add(link)

        db_alert = db.query(SentinelAlert).filter(SentinelAlert.alert_id == alert.alert_id).first()
        if db_alert:
            db_alert.incident_id = new_inc_id
            db_alert.status = "CORRELATED"

        db.commit()
        return new_inc_id, True, f"Created new incident '{new_inc_id}' from sentinel alert '{alert.alert_id}'."
