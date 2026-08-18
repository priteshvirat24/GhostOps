from typing import Set, Dict, Tuple
from app.schemas.remediation_execution import ExecutionStatus

class ExecutionStateMachine:
    """
    Deterministic State Machine for GhostOps Stage 6 Remediation Execution.
    Validates allowed state transitions and prevents illegal status jumps.
    """

    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        ExecutionStatus.PENDING: {ExecutionStatus.PRECHECKING, ExecutionStatus.CANCELLED, ExecutionStatus.BLOCKED},
        ExecutionStatus.PRECHECKING: {ExecutionStatus.READY, ExecutionStatus.BLOCKED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED},
        ExecutionStatus.READY: {ExecutionStatus.EXECUTING, ExecutionStatus.CANCELLED, ExecutionStatus.BLOCKED},
        ExecutionStatus.EXECUTING: {
            ExecutionStatus.VERIFYING,
            ExecutionStatus.FAILED,
            ExecutionStatus.ROLLING_BACK,
            ExecutionStatus.PAUSED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.COMPLETED
        },
        ExecutionStatus.PAUSED: {ExecutionStatus.EXECUTING, ExecutionStatus.CANCELLED, ExecutionStatus.ROLLING_BACK},
        ExecutionStatus.VERIFYING: {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.COMPLETED_WITH_WARNINGS,
            ExecutionStatus.FAILED,
            ExecutionStatus.ROLLING_BACK
        },
        ExecutionStatus.FAILED: {ExecutionStatus.ROLLING_BACK, ExecutionStatus.FAILED, ExecutionStatus.BLOCKED},
        ExecutionStatus.ROLLING_BACK: {ExecutionStatus.ROLLED_BACK, ExecutionStatus.ROLLBACK_FAILED},
        ExecutionStatus.ROLLED_BACK: set(),
        ExecutionStatus.ROLLBACK_FAILED: set(),
        ExecutionStatus.COMPLETED: set(),
        ExecutionStatus.COMPLETED_WITH_WARNINGS: set(),
        ExecutionStatus.CANCELLED: set(),
        ExecutionStatus.BLOCKED: set(),
    }

    @classmethod
    def validate_transition(cls, current_status: str, next_status: str) -> Tuple[bool, str]:
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, set())
        if next_status in allowed:
            return True, f"Valid transition from {current_status} to {next_status}"
        return False, f"Illegal state transition from '{current_status}' to '{next_status}'."
