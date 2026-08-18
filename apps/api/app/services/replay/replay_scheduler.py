import uuid
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class ReplayScheduler:
    """
    Deterministic In-Process Replay Scheduler for GhostOps Stage 8.
    Manages replay request queues, priorities (CRITICAL, HIGH, NORMAL, LOW), deduplication, and status tracking.
    """

    _QUEUE: List[Dict[str, Any]] = []
    _JOB_STATUS: Dict[str, Dict[str, Any]] = {}

    PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}

    @classmethod
    def enqueue_replay(
        cls,
        incident_id: str,
        mode: str = "HISTORICAL_REPLAY",
        priority: str = "NORMAL",
        counterfactual_params: Dict[str, Any] = None,
        memory_ids: List[str] = None
    ) -> str:
        req_hash = hashlib.sha256(json.dumps({
            "incident_id": incident_id,
            "mode": mode,
            "params": counterfactual_params or {}
        }, sort_keys=True).encode()).hexdigest()

        # Check for deduplication: if exact pending job exists, return existing job_id
        for job in cls._QUEUE:
            if job.get("hash") == req_hash and job.get("status") == "QUEUED":
                return job["job_id"]

        job_id = f"job-replay-{uuid.uuid4().hex[:10]}"
        job_item = {
            "job_id": job_id,
            "incident_id": incident_id,
            "mode": mode,
            "priority": priority,
            "counterfactual_params": counterfactual_params or {},
            "memory_ids": memory_ids or [],
            "hash": req_hash,
            "status": "QUEUED",
            "enqueued_at": datetime.now(timezone.utc).isoformat()
        }

        cls._QUEUE.append(job_item)
        # Sort queue by priority
        cls._QUEUE.sort(key=lambda j: cls.PRIORITY_ORDER.get(j["priority"], 2))
        cls._JOB_STATUS[job_id] = job_item
        return job_id

    @classmethod
    def get_queue(cls) -> List[Dict[str, Any]]:
        return list(cls._QUEUE)

    @classmethod
    def get_job_status(cls, job_id: str) -> Optional[Dict[str, Any]]:
        return cls._JOB_STATUS.get(job_id)

    @classmethod
    def clear_queue(cls):
        cls._QUEUE.clear()
        cls._JOB_STATUS.clear()
