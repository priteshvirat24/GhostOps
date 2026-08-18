from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.db.models import (
    RemediationExecution,
    ExecutionLockRecord,
    ReplayRun,
    SentinelInstance
)
from app.core.logging import logger

class ExecutionRecoveryService:
    """
    Execution Recovery & State Reconciliation Service for GhostOps Stage 10.
    Reconciles stale saga executions and expired locks stuck after API process crashes.
    """

    @classmethod
    def reconcile_stale_executions(cls, db: Session, timeout_seconds: int = 600) -> Dict[str, Any]:
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)

        # 1. Reconcile stale executions
        stale_execs = db.query(RemediationExecution).filter(
            RemediationExecution.status.in_(["EXECUTING", "VERIFYING", "COMPENSATING"]),
            RemediationExecution.updated_at <= cutoff_time
        ).all()

        exec_reconciled = 0
        for ex in stale_execs:
            ex.status = "FAILED"
            ex.failure_reason = "PROCESS_RESTART_RECONCILIATION: Execution timed out following API restart."
            ex.termination_reason = "RECONCILED_PROCESS_RESTART"
            ex.completed_at = datetime.now(timezone.utc)
            exec_reconciled += 1

        # 2. Release expired locks
        stale_locks = db.query(ExecutionLockRecord).filter(
            ExecutionLockRecord.status == "ACTIVE",
            ExecutionLockRecord.expires_at <= datetime.now(timezone.utc)
        ).all()

        locks_released = 0
        for lock in stale_locks:
            lock.status = "RELEASED"
            lock.released_at = datetime.now(timezone.utc)
            locks_released += 1

        db.commit()
        logger.info(f"[Recovery] Reconciled {exec_reconciled} stale executions and released {locks_released} expired locks.")

        return {
            "reconciled_executions_count": exec_reconciled,
            "released_locks_count": locks_released
        }

class ReplayRecoveryService:
    """
    Replay Run Recovery Service for GhostOps Stage 10.
    Reconciles stale replay runs stuck in SIMULATING or RECONSTRUCTING.
    """

    @classmethod
    def reconcile_stale_replays(cls, db: Session, timeout_seconds: int = 300) -> Dict[str, Any]:
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)

        stale_replays = db.query(ReplayRun).filter(
            ReplayRun.status.in_(["RECONSTRUCTING", "SIMULATING", "COMPARING"]),
            ReplayRun.started_at <= cutoff_time
        ).all()

        reconciled = 0
        for r in stale_replays:
            r.status = "FAILED"
            r.termination_reason = "RECONCILED_PROCESS_RESTART"
            r.completed_at = datetime.now(timezone.utc)
            reconciled += 1

        db.commit()
        return {"reconciled_replays_count": reconciled}

class SentinelRecoveryService:
    """
    Sentinel Recovery Service for GhostOps Stage 10.
    Reconciles sentinel state after process restart.
    """

    @classmethod
    def reconcile_sentinel_state(cls, db: Session) -> Dict[str, Any]:
        inst = db.query(SentinelInstance).filter(SentinelInstance.sentinel_id == "sentinel-primary").first()
        if inst and inst.status in ["STARTING", "RUNNING"]:
            inst.status = "RUNNING"
            inst.last_heartbeat_at = datetime.now(timezone.utc)
            db.commit()
            return {"sentinel_status": "RUNNING_RECONCILED"}
        return {"sentinel_status": "STOPPED"}
