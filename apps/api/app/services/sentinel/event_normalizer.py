import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any
from app.schemas.sentinel import SentinelEvent

class TelemetryEventNormalizer:
    """
    Telemetry Event Normalizer for GhostOps Stage 9.
    Normalizes signals from CloudWatch, CloudTrail, AWS Config, Stage 2 ingestion, and Stage 8 changefeed events into a canonical TelemetryEvent structure.
    """

    @classmethod
    def normalize_event(cls, raw_payload: Dict[str, Any], source: str = "CloudWatch") -> SentinelEvent:
        evt_id = raw_payload.get("event_id") or f"evt-norm-{uuid.uuid4().hex[:10]}"
        sentinel_id = raw_payload.get("sentinel_id", "sentinel-primary")

        evt_type = raw_payload.get("event_type") or raw_payload.get("detail-type") or "METRIC_ANOMALY"
        resource_id = raw_payload.get("resource_id") or raw_payload.get("target_resource_id") or "i-auth-ec2-01"
        resource_type = raw_payload.get("resource_type") or "EC2"

        severity = raw_payload.get("severity") or ("HIGH" if "CRITICAL" in str(raw_payload).upper() else "MEDIUM")
        metric_name = raw_payload.get("metric_name") or raw_payload.get("metric") or "CPUUtilization"

        metric_val = float(raw_payload.get("metric_value", raw_payload.get("value", 85.0)))
        baseline_val = float(raw_payload.get("baseline_value", 30.0))
        deviation = round(metric_val - baseline_val, 2)

        region = raw_payload.get("region", "us-east-1")
        timestamp_str = raw_payload.get("timestamp") or datetime.now(timezone.utc).isoformat()

        # Deterministic hashes & keys
        payload_bytes = json.dumps(raw_payload, sort_keys=True).encode()
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        fingerprint_str = f"{source}:{evt_type}:{resource_id}:{metric_name}"
        fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()

        dedup_key = f"{resource_id}:{metric_name}:{severity}"
        corr_key = f"{region}:{resource_id.split('-')[0] if '-' in resource_id else resource_id}"

        return SentinelEvent(
            event_id=evt_id,
            sentinel_id=sentinel_id,
            source=source,
            event_type=evt_type,
            resource_id=resource_id,
            resource_type=resource_type,
            timestamp=timestamp_str,
            severity=severity,
            metric_name=metric_name,
            metric_value=metric_val,
            baseline_value=baseline_val,
            deviation=deviation,
            region=region,
            fingerprint=fingerprint,
            payload_hash=payload_hash,
            correlation_key=corr_key,
            deduplication_key=dedup_key,
            suppressed=False,
            processed=False
        )
