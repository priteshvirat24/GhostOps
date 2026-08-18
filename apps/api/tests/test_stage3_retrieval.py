import pytest
import math
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.db.models import Incident, InfrastructureSnapshot, IncidentEvidence, OperationalActionHistory, InstitutionalMemoryVector
from app.services.retrieval import (
    IncidentFingerprint,
    StalenessCalculator,
    StructuredMemoryRetriever,
    VectorMemoryRetriever,
    HybridScorer,
    HistoricalRetrievalService,
)
from app.agents import MockBedrockProvider
from ghostops_shared import IncidentSeverity, IncidentStatus, TrustLevel

def test_incident_fingerprint_generation():
    inc = Incident(
        id="test-inc-fp",
        title="Database Connection Exhaustion Alarm",
        description="Test incident description",
        service="auth-service",
        region="us-east-1",
        severity=IncidentSeverity.HIGH,
        target_resource_id="i-test-01"
    )
    snap = InfrastructureSnapshot(
        incident_id="test-inc-fp",
        db_version="CockroachDB v23.2.3",
        service_version="v4.2.0"
    )
    evidence = [
        IncidentEvidence(
            incident_id="test-inc-fp",
            source="cloudwatch",
            source_event_id="cw-100",
            captured_at=datetime.now(timezone.utc),
            event_type="database_connection_exhaustion",
            raw_payload={"AlarmName": "DatabaseConnectionExhaustion"}
        )
    ]

    fp = IncidentFingerprint.from_incident(inc, snap, evidence)
    assert fp.service == "auth-service"
    assert fp.region == "us-east-1"
    assert fp.service_version == "v4.2.0"
    assert fp.db_version == "CockroachDB v23.2.3"
    assert "database_connection_exhaustion" in fp.symptoms

    text = fp.to_canonical_text()
    assert "auth-service" in text
    assert "database_connection_exhaustion" in text
    assert "CockroachDB v23.2.3" in text

def test_staleness_calculator():
    now = datetime.now(timezone.utc)
    # Brand new incident -> 0.0 penalty
    pen_new = StalenessCalculator.calculate_penalty(now, reference_time=now, half_life_days=180)
    assert pen_new == 0.0

    # 180 days old -> ~0.5 penalty
    past_180d = now - timedelta(days=180)
    pen_180d = StalenessCalculator.calculate_penalty(past_180d, reference_time=now, half_life_days=180)
    assert 0.49 <= pen_180d <= 0.51

    # 365 days old -> ~0.75 penalty
    past_365d = now - timedelta(days=365)
    pen_365d = StalenessCalculator.calculate_penalty(past_365d, reference_time=now, half_life_days=180)
    assert pen_365d > pen_180d

def test_hybrid_scorer_formula():
    # Test formula: (0.35 * struct) + (0.35 * vec) + (0.15 * outcome) + (0.10 * trust) - (0.05 * stale)
    score = HybridScorer.calculate_hybrid_score(
        structured_score=1.0,
        semantic_score=1.0,
        outcome_score=1.0,
        trust_score=1.0,
        staleness_penalty=0.0
    )
    # Total sum = 0.35 + 0.35 + 0.15 + 0.10 - 0 = 0.95
    assert score == 0.95

    # Test outcome evaluation
    actions_failed = [OperationalActionHistory(command="ecs:RestartService", tool="MockECSAdapter", target="auth-service", result="FAILED")]
    actions_success = [
        OperationalActionHistory(command="ecs:RestartService", tool="MockECSAdapter", target="auth-service", result="FAILED"),
        OperationalActionHistory(command="ec2:RevokeSecurityGroupIngress", tool="MockSSMAdapter", target="sg-01", result="SUCCESS")
    ]

    out_failed, sum_failed = HybridScorer.compute_outcome_score(actions_failed)
    out_succ, sum_succ = HybridScorer.compute_outcome_score(actions_success)

    assert out_failed == 0.0
    assert sum_failed == "ALL_ATTEMPTS_FAILED"
    assert out_succ == 1.0
    assert sum_succ == "SUCCESSFUL_REMEDIATION"

def test_golden_retrieval_ranking(db_session):
    provider = MockBedrockProvider()
    now_time = datetime.now(timezone.utc)

    # Seed Incidents A, B, C, D directly
    inc_a = Incident(
        id="inc-a-id", title="High CPU & Database Connection Exhaustion", description="Incident A description", service="auth-service",
        region="us-east-1", severity=IncidentSeverity.HIGH, status=IncidentStatus.RESOLVED,
        start_time=now_time, memory_status="COMPLETED"
    )
    inc_b = Incident(
        id="inc-b-id", title="Database Connection Exhaustion & Auth Timeout", description="Incident B description", service="auth-service",
        region="us-east-1", severity=IncidentSeverity.HIGH, status=IncidentStatus.RESOLVED,
        start_time=now_time - timedelta(days=1), memory_status="COMPLETED"
    )
    inc_c = Incident(
        id="inc-c-id", title="Database Connection Exhaustion on Billing Service", description="Incident C description", service="billing-service",
        region="us-east-1", severity=IncidentSeverity.MEDIUM, status=IncidentStatus.CLOSED,
        start_time=now_time - timedelta(days=7), memory_status="COMPLETED"
    )
    inc_d = Incident(
        id="inc-d-id", title="Unauthorized API Access Anomaly", description="Incident D description", service="auth-service",
        region="us-east-1", severity=IncidentSeverity.LOW, status=IncidentStatus.RESOLVED,
        start_time=now_time - timedelta(days=14), memory_status="COMPLETED"
    )
    db_session.add_all([inc_a, inc_b, inc_c, inc_d])
    db_session.flush()

    # Add Snapshots
    snap_a = InfrastructureSnapshot(incident_id=inc_a.id, db_version="CockroachDB v23.2.3", service_version="v4.2.0")
    snap_b = InfrastructureSnapshot(incident_id=inc_b.id, db_version="CockroachDB v23.2.3", service_version="v4.1.0")
    snap_c = InfrastructureSnapshot(incident_id=inc_c.id, db_version="PostgreSQL v14.0", service_version="v3.0.0")
    snap_d = InfrastructureSnapshot(incident_id=inc_d.id, db_version="CockroachDB v23.2.3", service_version="v4.2.0")
    db_session.add_all([snap_a, snap_b, snap_c, snap_d])

    # Add Actions (Incident A has 2 failed actions and 1 successful action)
    db_session.add(OperationalActionHistory(incident_id=inc_a.id, command="ecs:RestartService", tool="MockECSAdapter", target="auth-service", result="FAILED", reason="Attempt 1 failed", idempotency_key="act-a1"))
    db_session.add(OperationalActionHistory(incident_id=inc_a.id, command="ec2:ModifyInstanceAttribute", tool="MockEC2Adapter", target="i-test", result="FAILED", reason="Attempt 2 failed", idempotency_key="act-a2"))
    db_session.add(OperationalActionHistory(incident_id=inc_a.id, command="ec2:RevokeSecurityGroupIngress", tool="MockSSMAdapter", target="sg-01", result="SUCCESS", reason="Attempt 3 succeeded", idempotency_key="act-a3"))

    db_session.add(OperationalActionHistory(incident_id=inc_b.id, command="cockroach:RestartClusterNode", tool="MockCRDBAdapter", target="crdb-01", result="FAILED", reason="Attempt 1 failed", idempotency_key="act-b1"))
    db_session.add(OperationalActionHistory(incident_id=inc_b.id, command="secretsmanager:RotateSecret", tool="MockSMAdapter", target="sec-01", result="SUCCESS", reason="Attempt 2 succeeded", idempotency_key="act-b2"))

    db_session.add(OperationalActionHistory(incident_id=inc_c.id, command="ecs:RestartService", tool="MockECSAdapter", target="billing-service", result="FAILED", reason="Attempt 1 failed", idempotency_key="act-c1"))
    db_session.add(OperationalActionHistory(incident_id=inc_d.id, command="iam:PutRolePolicy", tool="MockIAMAdapter", target="role-01", result="SUCCESS", reason="Attempt 1 succeeded", idempotency_key="act-d1"))

    # Add Evidence
    ev_a = IncidentEvidence(incident_id=inc_a.id, source="cloudwatch", source_event_id="cw-a", captured_at=now_time, event_type="database_connection_exhaustion", content_hash="hash-a", raw_payload={})
    ev_b = IncidentEvidence(incident_id=inc_b.id, source="cloudwatch", source_event_id="cw-b", captured_at=now_time, event_type="database_connection_exhaustion", content_hash="hash-b", raw_payload={})
    ev_c = IncidentEvidence(incident_id=inc_c.id, source="cloudwatch", source_event_id="cw-c", captured_at=now_time, event_type="database_connection_exhaustion", content_hash="hash-c", raw_payload={})
    ev_d = IncidentEvidence(incident_id=inc_d.id, source="cloudtrail", source_event_id="ct-d", captured_at=now_time, event_type="unauthorized_api_call", content_hash="hash-d", raw_payload={})
    db_session.add_all([ev_a, ev_b, ev_c, ev_d])
    db_session.flush()

    # Generate Embeddings (A, B, C share database_connection_exhaustion semantic vector digest, D uses unauthorized_api_call)
    symptom_vector_db = provider.generate_embedding("database_connection_exhaustion")
    symptom_vector_api = provider.generate_embedding("unauthorized_api_call")

    db_session.add(InstitutionalMemoryVector(title="A", content="A", memory_type="remediation", incident_id=inc_a.id, embedding=symptom_vector_db))
    db_session.add(InstitutionalMemoryVector(title="B", content="B", memory_type="remediation", incident_id=inc_b.id, embedding=symptom_vector_db))
    db_session.add(InstitutionalMemoryVector(title="C", content="C", memory_type="symptom", incident_id=inc_c.id, embedding=symptom_vector_db))
    db_session.add(InstitutionalMemoryVector(title="D", content="D", memory_type="remediation", incident_id=inc_d.id, embedding=symptom_vector_api))
    db_session.commit()

    # Create target query incident identical to A
    target_inc = Incident(
        id="target-query-id", title="Database Connection Exhaustion Alarm", description="Target description",
        service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time
    )
    db_session.add(target_inc)
    db_session.add(InfrastructureSnapshot(incident_id=target_inc.id, db_version="CockroachDB v23.2.3", service_version="v4.2.0"))
    db_session.add(IncidentEvidence(incident_id=target_inc.id, source="cloudwatch", source_event_id="cw-target", captured_at=now_time, event_type="database_connection_exhaustion", content_hash="hash-t", raw_payload={}))
    db_session.commit()

    # Execute Hybrid Retrieval Service
    res = HistoricalRetrievalService.get_similar_incidents(
        db=db_session,
        incident_id="target-query-id",
        limit=5,
        include_failed_actions=True
    )

    assert res.target_incident_id == "target-query-id"
    assert res.candidates_count == 4
    candidates = res.candidates

    # MANDATORY GOLDEN RANKING ORDER VERIFICATION: A > B > C > D
    rank_1 = candidates[0]
    rank_2 = candidates[1]
    rank_3 = candidates[2]
    rank_4 = candidates[3]

    assert rank_1.incident_id == inc_a.id
    assert rank_2.incident_id == inc_b.id
    assert rank_3.incident_id == inc_c.id
    assert rank_4.incident_id == inc_d.id

    # Verify A's failed actions and successful actions are PRESERVED!
    assert len(rank_1.failed_actions) == 2
    assert len(rank_1.successful_actions) == 1
    assert rank_1.failed_actions[0]["command"] == "ecs:RestartService"
    assert rank_1.failed_actions[1]["command"] == "ec2:ModifyInstanceAttribute"
    assert rank_1.successful_actions[0]["command"] == "ec2:RevokeSecurityGroupIngress"

    # Verify A's explainable matched fields checklist
    assert rank_1.matched_fields["service"] is True
    assert rank_1.matched_fields["region"] is True
    assert rank_1.matched_fields["db_version"] is True
    assert rank_1.matched_fields["service_version"] is True

def test_similar_incidents_api_endpoint(client, db_session):
    now_time = datetime.now(timezone.utc)
    inc1 = Incident(id="api-inc-1", title="Auth Service Spike", description="Desc 1", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    inc2 = Incident(id="api-inc-2", title="Auth Service Outage", description="Desc 2", service="auth-service", region="us-east-1", severity=IncidentSeverity.HIGH, start_time=now_time)
    db_session.add_all([inc1, inc2])
    db_session.commit()

    res = client.get("/api/v1/incidents/api-inc-1/similar?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert data["target_incident_id"] == "api-inc-1"
    assert data["candidates_count"] == 1
    assert data["candidates"][0]["incident_id"] == "api-inc-2"

def test_memory_search_api_endpoint(client, db_session):
    provider = MockBedrockProvider()
    vec = provider.generate_embedding("search memory query text test")
    mem = InstitutionalMemoryVector(
        id="mem-search-1",
        title="Search Test Memory",
        content="search memory content",
        memory_type="symptom",
        incident_id="inc-search-1",
        embedding=vec
    )
    db_session.add(mem)
    db_session.commit()

    search_payload = {
        "query_text": "search memory query text test",
        "limit": 5
    }
    res = client.post("/api/v1/memory/search", json=search_payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["memory_id"] == "mem-search-1"
    assert data[0]["similarity_score"] > 0.8
