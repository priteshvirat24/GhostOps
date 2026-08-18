import uuid
import hashlib
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.db.models import InstitutionalMemoryVector
from app.services.replay.replay_scheduler import ReplayScheduler

class InfrastructureChangefeedMonitor:
    """
    Infrastructure Changefeed Monitor for GhostOps Stage 8.
    Listens for infrastructure state change events and enqueues replay validation jobs.
    """

    @classmethod
    def process_change_event(
        cls,
        db: Session,
        event_type: str,
        resource_id: str,
        change_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Query active memories linked to this resource or service
        affected_memories = db.query(InstitutionalMemoryVector).filter(
            InstitutionalMemoryVector.memory_status == "ACTIVE"
        ).limit(5).all()

        mem_ids = [m.id for m in affected_memories]

        # Enqueue validation replay job
        job_id = ReplayScheduler.enqueue_replay(
            incident_id=change_metadata.get("incident_id", "inc-01"),
            mode="INFRASTRUCTURE_DRIFT_SIMULATION",
            priority="HIGH",
            counterfactual_params=change_metadata,
            memory_ids=mem_ids
        )

        return {
            "change_event_id": f"evt-change-{uuid.uuid4().hex[:8]}",
            "event_type": event_type,
            "resource_id": resource_id,
            "affected_memories": mem_ids,
            "enqueued_job_id": job_id,
            "status": "QUEUED"
        }
