import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone, timedelta
from app.core.errors import GhostOpsException

class CircuitState(str):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    """
    Circuit Breaker for GhostOps Stage 10.
    Protects CockroachDB, AWS adapters, Bedrock model provider, and replay scheduler against cascading failures.
    """

    def __init__(self, name: str, failure_threshold: int = 5, cooldown_seconds: int = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        now = datetime.now(timezone.utc)

        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (now - self.last_failure_time).total_seconds() > self.cooldown_seconds:
                self.state = CircuitState.HALF_OPEN
            else:
                raise GhostOpsException(
                    error_code="CIRCUIT_BREAKER_OPEN",
                    message=f"Circuit breaker '{self.name}' is OPEN. Requests blocked during cooldown window.",
                    status_code=503
                )

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now(timezone.utc)
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            raise e
