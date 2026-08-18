import logging
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class StructuredJSONFormatter(logging.Formatter):
    """
    Structured JSON Formatter for GhostOps Stage 10.
    Produces machine-readable JSON logs with correlation ID propagation and secret redaction.
    """

    @staticmethod
    def redact_secrets(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redacts sensitive credentials, tokens, and authorization keys."""
        SENSITIVE_KEYS = ["secret", "password", "token", "key", "authorization", "bearer", "private"]
        redacted = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                redacted[k] = "[REDACTED_SECRET]"
            elif isinstance(v, dict):
                redacted[k] = StructuredJSONFormatter.redact_secrets(v)
            else:
                redacted[k] = v
        return redacted

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "ghostops-api",
            "message": record.getMessage(),
            "logger": record.name
        }

        # Extra correlation identifiers
        for field in ["event_type", "request_id", "incident_id", "plan_id", "execution_id", "replay_id", "sentinel_run_id", "trace_id", "actor"]:
            if hasattr(record, field):
                log_obj[field] = getattr(record, field)

        # Redact any secrets in extra payload details
        if hasattr(record, "details") and isinstance(record.details, dict):
            log_obj["details"] = self.redact_secrets(record.details)

        return json.dumps(log_obj)

def setup_structured_logging():
    logger = logging.getLogger("ghostops")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJSONFormatter())
        logger.addHandler(handler)

    return logger

logger = setup_structured_logging()
