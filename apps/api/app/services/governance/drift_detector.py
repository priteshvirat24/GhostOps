from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import InfrastructureSnapshot, Incident

class DriftDetector:
    """
    Drift Detector for GhostOps Stage 5.
    Compares point-in-time infrastructure snapshot captured at investigation start
    against current baseline infrastructure before a plan becomes READY_FOR_EXECUTION.
    """

    @staticmethod
    def detect_drift(
        db: Session,
        incident_id: str,
        investigation_snapshot: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        factors: List[str] = []

        if not investigation_snapshot:
            return False, []

        # Query latest current snapshot baseline from DB
        current_snap = db.scalars(
            select(InfrastructureSnapshot)
            .where(InfrastructureSnapshot.incident_id == incident_id)
            .order_by(InfrastructureSnapshot.snapshot_timestamp.desc())
        ).first()

        if not current_snap:
            return False, []

        # Check Service Version Drift
        inv_svc_ver = investigation_snapshot.get("service_version")
        curr_svc_ver = current_snap.service_version
        if inv_svc_ver and curr_svc_ver and inv_svc_ver != curr_svc_ver:
            factors.append(f"Service version drift detected: investigated '{inv_svc_ver}' vs current baseline '{curr_svc_ver}'")

        # Check DB Version Drift
        inv_db_ver = investigation_snapshot.get("db_version")
        curr_db_ver = current_snap.db_version
        if inv_db_ver and curr_db_ver and inv_db_ver != curr_db_ver:
            factors.append(f"Database version drift detected: investigated '{inv_db_ver}' vs current baseline '{curr_db_ver}'")

        # Check Configuration Pool Drift
        inv_pool = investigation_snapshot.get("configuration", {}).get("pool")
        curr_pool = current_snap.configuration.get("pool") if current_snap.configuration else None
        if inv_pool is not None and curr_pool is not None and inv_pool != curr_pool:
            factors.append(f"Configuration pool drift detected: investigated pool {inv_pool} vs current pool {curr_pool}")

        drift_detected = len(factors) > 0
        return drift_detected, factors
