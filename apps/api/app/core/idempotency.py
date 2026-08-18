import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from app.core.errors import GhostOpsException

class IdempotencyManager:
    """
    Idempotency Manager for GhostOps Stage 10.
    Prevents duplicate state transitions and duplicate execution requests across all mutation endpoints.
    """

    _CACHE: Dict[str, Dict[str, Any]] = {}
    _TTL_SECONDS: int = 86400

    @classmethod
    def generate_key(cls, endpoint: str, payload: Dict[str, Any]) -> str:
        raw_str = f"{endpoint}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.sha256(raw_str.encode()).hexdigest()

    @classmethod
    def check_idempotency(cls, idempotency_key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        if idempotency_key in cls._CACHE:
            record = cls._CACHE[idempotency_key]
            # Check expiration
            if datetime.now(timezone.utc) < record["expires_at"]:
                return True, record["response_payload"]
            else:
                del cls._CACHE[idempotency_key]
        return False, None

    @classmethod
    def record_idempotency(cls, idempotency_key: str, response_payload: Dict[str, Any]):
        exp = datetime.now(timezone.utc) + timedelta(seconds=cls._TTL_SECONDS)
        cls._CACHE[idempotency_key] = {
            "response_payload": response_payload,
            "expires_at": exp,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    def clear_cache(cls):
        cls._CACHE.clear()
