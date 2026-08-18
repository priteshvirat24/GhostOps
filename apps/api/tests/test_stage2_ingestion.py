import pytest
import json
import hashlib
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy.exc import IntegrityError
from app.core.redaction import redact_secrets
from app.agents import MockBedrockProvider
from app.services.normalizer import EventNormalizer
from app.services.ingestion_service import IncidentIngestionService
from app.db.models import OperationalActionHistory, IncidentEvidence, Incident

def test_redaction_utility():
    raw_text = "API Key AKIAIOSFODNN7EXAMPLE and secret=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY and Bearer eyJhbGciOi..."
    redacted = redact_secrets(raw_text)
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "wJalrXUtnFEMI" not in redacted
    assert "[REDACTED_AWS_KEY_ID]" in redacted

def test_deterministic_normalizer():
    cw_payload = {
        "AlarmName": "HighCPUUtilization-EC2-prod-web-01",
        "StateValue": "ALARM",
        "MetricName": "CPUUtilization",
        "Namespace": "AWS/EC2",
        "Dimensions": [{"Name": "InstanceId", "Value": "i-0a1b2c3d4e5f6g7h8"}],
        "Timestamp": "2026-08-17T22:00:00Z"
    }
    norm1 = EventNormalizer.normalize_event(cw_payload)
    norm2 = EventNormalizer.normalize_event(cw_payload)

    assert norm1.source == "cloudwatch"
    assert norm1.severity == "HIGH"
    assert norm1.resource_id == "i-0a1b2c3d4e5f6g7h8"
    assert norm1.timestamp == norm2.timestamp
    assert norm1.event_id == norm2.event_id

def test_deterministic_embedding_provider():
    provider = MockBedrockProvider()
    input_text = "database connection exhaustion caused elevated authentication latency"
    
    vec1 = provider.generate_embedding(input_text)
    vec2 = provider.generate_embedding(input_text)
    vec_diff = provider.generate_embedding("completely different telemetry payload")

    assert len(vec1) == 1536
    assert vec1 == vec2  # Exactly identical vectors for identical inputs!
    assert vec1 != vec_diff  # Different vectors for different inputs

def test_action_idempotency_constraint(db_session):
    act1 = OperationalActionHistory(
        incident_id="dummy-inc-id",
        command="ecs:RestartService",
        tool="MockECSAdapter",
        target="prod-web-service",
        reason="Attempt 1 restart",
        idempotency_key="unique-idempotency-key-100",
        result="FAILED"
    )
    db_session.add(act1)
    db_session.commit()

    # Attempt to insert identical idempotency key
    act2 = OperationalActionHistory(
        incident_id="dummy-inc-id",
        command="ecs:RestartService",
        tool="MockECSAdapter",
        target="prod-web-service",
        reason="Attempt 2 duplicate",
        idempotency_key="unique-idempotency-key-100",
        result="FAILED"
    )
    db_session.add(act2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_ingestion_pipeline_and_duplicate_handling(db_session):
    raw_events = [
        {
            "AlarmName": "HighCPUUtilization-EC2-prod-web-01",
            "StateValue": "ALARM",
            "MetricName": "CPUUtilization",
            "Dimensions": [{"Name": "InstanceId", "Value": "i-0a1b2c3d4e5f6g7h8"}],
            "Timestamp": "2026-08-17T22:00:00Z"
        },
        {
            "eventName": "AuthorizeSecurityGroupIngress",
            "eventSource": "ec2.amazonaws.com",
            "eventTime": "2026-08-17T21:55:00Z",
            "requestParameters": {"groupId": "sg-0123456789abcdef0"}
        }
    ]

    actions = [
        {"command": "ecs:RestartService", "result": "FAILED", "reason": "Attempt 1 failed"},
        {"command": "ec2:RevokeSecurityGroupIngress", "result": "SUCCESS", "reason": "Attempt 2 succeeded"}
    ]

    # Ingest first time
    res1 = IncidentIngestionService.ingest_operational_events(
        db=db_session,
        raw_events=raw_events,
        target_service="prod-web-service",
        region="us-east-1",
        actions_data=actions
    )

    assert res1.events_received == 2
    assert res1.events_created == 2
    assert res1.duplicate_events == 0
    assert res1.status == "COMPLETED"

    # Verify failed action is preserved in DB!
    actions_in_db = db_session.query(OperationalActionHistory).filter_by(incident_id=res1.incident_id).all()
    assert len(actions_in_db) == 2
    failed_action = [a for a in actions_in_db if a.result == "FAILED"]
    assert len(failed_action) == 1
    assert failed_action[0].command == "ecs:RestartService"

    # Ingest exact same events second time -> should report duplicates!
    res2 = IncidentIngestionService.ingest_operational_events(
        db=db_session,
        raw_events=raw_events,
        target_service="prod-web-service",
        region="us-east-1"
    )

    assert res2.events_received == 2
    assert res2.events_created == 0
    assert res2.duplicate_events == 2

def test_ingestion_api_endpoints(client):
    payload = {
        "events": [
            {
                "AlarmName": "HighCPUUtilization-API-Test",
                "StateValue": "ALARM",
                "MetricName": "CPUUtilization",
                "Dimensions": [{"Name": "InstanceId", "Value": "i-api-test-01"}],
                "Timestamp": "2026-08-17T22:30:00Z"
            }
        ],
        "target_service": "auth-service",
        "region": "us-east-1"
    }

    # Test POST /api/v1/incidents/ingest
    ingest_res = client.post("/api/v1/incidents/ingest", json=payload)
    assert ingest_res.status_code == 201
    ingest_data = ingest_res.json()
    incident_id = ingest_data["incident_id"]
    assert ingest_data["events_created"] == 1

    # Test GET /api/v1/incidents/{incident_id}
    detail_res = client.get(f"/api/v1/incidents/{incident_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["service"] == "auth-service"
    assert len(detail_data["snapshots"]) == 1

    # Test GET /api/v1/incidents/{incident_id}/evidence
    ev_res = client.get(f"/api/v1/incidents/{incident_id}/evidence")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert len(ev_data) == 1
    assert "content_hash" in ev_data[0]

    # Test GET /api/v1/incidents/{incident_id}/timeline
    tl_res = client.get(f"/api/v1/incidents/{incident_id}/timeline")
    assert tl_res.status_code == 200
    assert len(tl_res.json()) == 1

    # Test GET /api/v1/incidents/{incident_id}/summary
    sum_res = client.get(f"/api/v1/incidents/{incident_id}/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["service"] == "auth-service"
    assert sum_data["events_count"] == 1

def test_embedding_failure_state_handling(db_session):
    raw_events = [{
        "AlarmName": "TestEmbeddingFailureAlarm",
        "StateValue": "ALARM",
        "Timestamp": "2026-08-17T22:40:00Z"
    }]

    # Patch generate_embedding to raise exception
    with patch("app.agents.model_provider.MockBedrockProvider.generate_embedding", side_effect=RuntimeError("Bedrock connection timeout")):
        result = IncidentIngestionService.ingest_operational_events(
            db=db_session,
            raw_events=raw_events
        )

        assert result.status == "MEMORY_DEGRADED"
        # Incident and evidence remain safely created in database!
        inc = db_session.get(Incident, result.incident_id)
        assert inc is not None
        assert inc.memory_status == "MEMORY_DEGRADED"
