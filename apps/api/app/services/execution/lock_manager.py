import uuid
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.db.models import ExecutionLockRecord
from app.schemas.remediation_execution import LockStatus

class ExecutionLockManager:
    """
    Distributed-safe logical execution lock manager for GhostOps Stage 6.
    Prevents concurrent executions from mutating the same resource target simultaneously.
    """

    @classmethod
    def acquire_lock(
        cls,
        db: Session,
        resource_scope: str,
        plan_id: str,
        execution_id: str,
        ttl_minutes: int = 30
    ) -> Tuple[bool, Optional[ExecutionLockRecord], str]:
        now_time = datetime.now(timezone.utc)
        expires_time = now_time + timedelta(minutes=ttl_minutes)

        # Check existing lock for scope
        existing_lock = db.scalars(
            select(ExecutionLockRecord).where(
                and_(
                    ExecutionLockRecord.resource_scope == resource_scope,
                    ExecutionLockRecord.status == LockStatus.ACTIVE
                )
            )
        ).first()

        if existing_lock:
            # Check if existing lock is expired
            lock_exp = existing_lock.expires_at.replace(tzinfo=timezone.utc) if existing_lock.expires_at.tzinfo is None else existing_lock.expires_at
            if now_time > lock_exp:
                existing_lock.status = LockStatus.EXPIRED
                existing_lock.released_at = now_time
                db.commit()
            else:
                return False, None, f"EXECUTION_BLOCKED_BY_LOCK: Active lock '{existing_lock.id}' owned by execution '{existing_lock.execution_id}'."

        lock_id = f"lock-{uuid.uuid4().hex[:12]}"
        new_lock = ExecutionLockRecord(
            id=lock_id,
            resource_scope=resource_scope,
            plan_id=plan_id,
            execution_id=execution_id,
            status=LockStatus.ACTIVE,
            acquired_at=now_time,
            expires_at=expires_time
        )
        db.add(new_lock)
        db.commit()

        return True, new_lock, f"Execution lock '{lock_id}' acquired for scope '{resource_scope}'."

    @classmethod
    def release_lock(cls, db: Session, lock_id: str) -> bool:
        if not lock_id:
            return True
        lock = db.get(ExecutionLockRecord, lock_id)
        if lock and lock.status == LockStatus.ACTIVE:
            lock.status = LockStatus.RELEASED
            lock.released_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False
