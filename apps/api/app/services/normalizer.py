import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from ghostops_shared import IncidentSeverity
from app.schemas.normalized_event import NormalizedOperationalEvent

class EventNormalizer:
    """
    Deterministic telemetry event normalizer for CloudWatch, CloudTrail, and AWS Config.
    Converts raw heterogeneous JSON payloads into strongly typed NormalizedOperationalEvents.
    """

    @staticmethod
    def normalize_event(raw_event: Dict[str, Any]) -> NormalizedOperationalEvent:
        # 1. CloudWatch Alarm event pattern
        if "AlarmName" in raw_event or raw_event.get("eventSource") == "cloudwatch":
            alarm_name = raw_event.get("AlarmName", "CloudWatchAlarm")
            state_val = raw_event.get("StateValue", "ALARM")
            metric_name = raw_event.get("MetricName", "UnknownMetric")

            dimensions = raw_event.get("Dimensions", [])
            resource_id = "unknown-resource"
            for dim in dimensions:
                if dim.get("Name") in ("InstanceId", "DBInstanceIdentifier", "ServiceName", "ResourceId"):
                    resource_id = dim.get("Value")
                    break

            severity = IncidentSeverity.HIGH if state_val == "ALARM" else IncidentSeverity.MEDIUM
            ts_str = raw_event.get("Timestamp")
            ts = EventNormalizer._parse_timestamp(ts_str)

            event_id = raw_event.get("EventId") or f"cw-{hash(alarm_name + str(ts_str)) & 0xffffffff:08x}"

            return NormalizedOperationalEvent(
                event_id=event_id,
                source="cloudwatch",
                event_type="ALARM_TRIGGERED",
                timestamp=ts,
                service=raw_event.get("Namespace", "aws-cloudwatch").lower().replace("aws/", ""),
                region=raw_event.get("Region", "us-east-1"),
                resource_id=resource_id,
                severity=severity,
                message=f"CloudWatch Alarm '{alarm_name}' state changed to {state_val} for metric {metric_name}",
                raw_payload=raw_event,
                metadata={"alarm_name": alarm_name, "metric_name": metric_name, "state": state_val}
            )

        # 2. CloudTrail Audit Event pattern
        if "eventName" in raw_event or raw_event.get("eventSource", "").endswith(".amazonaws.com"):
            event_name = raw_event.get("eventName", "CloudTrailEvent")
            event_source = raw_event.get("eventSource", "aws.cloudtrail")
            user_arn = raw_event.get("userIdentity", {}).get("arn", "unknown-actor")

            req_params = raw_event.get("requestParameters", {}) or {}
            resource_id = (
                req_params.get("groupId") or
                req_params.get("instanceId") or
                req_params.get("functionName") or
                "aws-account-resource"
            )

            ts_str = raw_event.get("eventTime")
            ts = EventNormalizer._parse_timestamp(ts_str)

            event_id = raw_event.get("eventID") or f"ct-{hash(event_name + str(ts_str)) & 0xffffffff:08x}"

            return NormalizedOperationalEvent(
                event_id=event_id,
                source="cloudtrail",
                event_type="API_AUDIT_LOG",
                timestamp=ts,
                service=event_source.split(".")[0],
                region=raw_event.get("awsRegion", "us-east-1"),
                resource_id=resource_id,
                severity=IncidentSeverity.MEDIUM,
                message=f"CloudTrail API call '{event_name}' executed by {user_arn}",
                raw_payload=raw_event,
                metadata={"actor": user_arn, "event_name": event_name}
            )

        # 3. AWS Config Snapshot pattern
        if "resourceId" in raw_event or raw_event.get("resourceType", "").startswith("AWS::"):
            resource_id = raw_event.get("resourceId", "config-resource")
            resource_type = raw_event.get("resourceType", "AWS::Resource")
            tags = raw_event.get("tags", {})
            service = tags.get("Service", resource_type.split("::")[-1].lower())

            ts_str = raw_event.get("captureTime") or raw_event.get("configurationItemCaptureTime")
            ts = EventNormalizer._parse_timestamp(ts_str)

            event_id = raw_event.get("arn") or f"cfg-{hash(resource_id + str(ts_str)) & 0xffffffff:08x}"

            return NormalizedOperationalEvent(
                event_id=event_id,
                source="aws_config",
                event_type="RESOURCE_CONFIG_SNAPSHOT",
                timestamp=ts,
                service=service,
                region=raw_event.get("awsRegion", "us-east-1"),
                resource_id=resource_id,
                severity=IncidentSeverity.LOW,
                message=f"AWS Config snapshot captured for {resource_type} '{resource_id}'",
                raw_payload=raw_event,
                metadata={"resource_type": resource_type, "tags": tags}
            )

        # Fallback generic event normalizer
        event_id = raw_event.get("event_id") or f"evt-{uuid.uuid4()}"
        return NormalizedOperationalEvent(
            event_id=event_id,
            source=raw_event.get("source", "generic"),
            event_type=raw_event.get("event_type", "GENERIC_TELEMETRY"),
            timestamp=EventNormalizer._parse_timestamp(raw_event.get("timestamp")),
            service=raw_event.get("service", "web-service"),
            region=raw_event.get("region", "us-east-1"),
            resource_id=raw_event.get("resource_id", "unknown-resource"),
            severity=IncidentSeverity(raw_event.get("severity", "MEDIUM")),
            message=raw_event.get("message", "Telemetry observation captured"),
            raw_payload=raw_event,
            metadata=raw_event.get("metadata", {})
        )

    @staticmethod
    def _parse_timestamp(ts_val: Any) -> datetime:
        if isinstance(ts_val, datetime):
            return ts_val if ts_val.tzinfo else ts_val.replace(tzinfo=timezone.utc)
        if isinstance(ts_val, str):
            try:
                dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        return datetime.now(timezone.utc)
