import time
from typing import Callable, Any, Type, Tuple
from app.core.errors import GhostOpsException

class ErrorClassification(str):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    SAFETY_BLOCK = "SAFETY_BLOCK"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    DRIFT_BLOCK = "DRIFT_BLOCK"
    CONFLICT = "CONFLICT"
    TIMEOUT = "TIMEOUT"

class RetryPolicy:
    """
    Classified Retry Policy for GhostOps Stage 10.
    Retries only TRANSIENT failures with exponential backoff.
    Fails fast on SAFETY_BLOCK, AUTHORIZATION_ERROR, DRIFT_BLOCK, and CONFLICT.
    """

    @classmethod
    def classify_exception(cls, exc: Exception) -> str:
        if isinstance(exc, GhostOpsException):
            if exc.error_code in ["AUTONOMOUS_EXECUTION_FORBIDDEN", "UNAUTHORIZED_ACTION"]:
                return ErrorClassification.AUTHORIZATION_ERROR
            if exc.error_code in ["PLAN_BLOCKED_BY_DRIFT", "SAFETY_CHECK_FAILED"]:
                return ErrorClassification.SAFETY_BLOCK
            if exc.error_code in ["EXECUTION_LOCK_CONFLICT", "PLAN_ALREADY_APPROVED"]:
                return ErrorClassification.CONFLICT
            if exc.error_code in ["CIRCUIT_BREAKER_OPEN", "NETWORK_TIMEOUT"]:
                return ErrorClassification.TRANSIENT

        exc_str = str(exc).lower()
        if "timeout" in exc_str or "connection reset" in exc_str or "503" in exc_str:
            return ErrorClassification.TRANSIENT

        return ErrorClassification.PERMANENT

    @classmethod
    def execute_with_retry(
        cls,
        func: Callable,
        max_attempts: int = 3,
        base_delay_seconds: float = 0.5,
        *args, **kwargs
    ) -> Any:
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                return func(*args, **kwargs)
            except Exception as e:
                classification = cls.classify_exception(e)
                if classification != ErrorClassification.TRANSIENT or attempt >= max_attempts:
                    raise e
                time.sleep(base_delay_seconds * (2 ** (attempt - 1)))
