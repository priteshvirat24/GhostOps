import os
import sys
import uuid
import json
import hashlib
from datetime import datetime, timezone

# Add apps/api and packages/shared to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "shared", "src")))

from sqlalchemy.orm import Session
from ghostops_shared import IncidentSeverity, IncidentStatus, EntityType, TrustLevel
from app.db.session import engine, SessionLocal
from app.db.models import (
    Base,
    Incident,
    IncidentEvent,
    IncidentEvidence,
    InfrastructureNode,
    InfrastructureSnapshot,
    OperationalActionHistory,
    InstitutionalMemoryVector,
)
from app.agents import MockBedrockProvider
from app.core.redaction import redact_secrets

def seed_database():
    print("Initializing CockroachDB tables...")
    Base.metadata.create_all(bind=engine)

    if "--init-only" in sys.argv:
        print("Schema initialized successfully!")
        return

    db: Session = SessionLocal()
    try:
        if db.query(Incident).first():
            print("Database already contains seed data. Skipping.")
            return

        print("Seeding GhostOps Stage 3 Golden Retrieval Dataset (Incidents A, B, C, D)...")
        provider = MockBedrockProvider()

        # =====================================================================
        # INCIDENT A (Gold Rank 1 Candidate for A-like query)
        # =====================================================================
        start_a = datetime.fromisoformat("2026-08-17T21:30:00+00:00")
        inc_a = Incident(
            title="High CPU Utilization & Database Connection Exhaustion",
            description="auth-service CPU exceeded 94% threshold following port 22 ingress rule addition.",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.RESOLVED,
            service="auth-service",
            region="us-east-1",
            start_time=start_a,
            end_time=datetime.fromisoformat("2026-08-17T22:15:00+00:00"),
            target_resource_id="i-auth-ec2-01",
            environment_fingerprint={"service": "auth-service", "region": "us-east-1"},
            root_cause_summary="Unrestricted SSH port 22 ingress enabled external brute-force surge, leading to connection exhaustion.",
            memory_status="COMPLETED"
        )
        db.add(inc_a)
        db.flush()

        raw_a = {"AlarmName": "DatabaseConnectionExhaustion", "StateValue": "ALARM", "Service": "auth-service"}
        hash_a = hashlib.sha256(json.dumps(raw_a, sort_keys=True).encode("utf-8")).hexdigest()
        ev_a = IncidentEvidence(
            incident_id=inc_a.id, source="cloudwatch", source_event_id="cw-inc-a",
            captured_at=start_a, event_type="database_connection_exhaustion",
            raw_payload=raw_a, content_hash=hash_a, trust_level=TrustLevel.MEDIUM
        )
        db.add(ev_a)

        db.add(InfrastructureSnapshot(
            incident_id=inc_a.id, snapshot_timestamp=start_a, db_version="CockroachDB v23.2.3",
            service_version="v4.2.0", topology={"service": "auth-service"}, configuration={"pool": 50},
            dependencies={"db": "crdb-cluster"}, resource_identifiers=["i-auth-ec2-01"], region="us-east-1", traffic_info={}
        ))

        db.add(OperationalActionHistory(
            incident_id=inc_a.id, actor="GhostOps", command="ecs:RestartService", tool="MockECSAdapter",
            target="auth-service", reason="Restart service attempt", idempotency_key=f"act-a1-{uuid.uuid4()}",
            result="FAILED", error_message="Restart failed to lower CPU; ingress surge persists.", timestamp=start_a
        ))
        db.add(OperationalActionHistory(
            incident_id=inc_a.id, actor="GhostOps", command="ec2:ModifyInstanceAttribute", tool="MockEC2Adapter",
            target="i-auth-ec2-01", reason="Memory pool expansion attempt", idempotency_key=f"act-a2-{uuid.uuid4()}",
            result="FAILED", error_message="Instance family constraints.", timestamp=start_a
        ))
        db.add(OperationalActionHistory(
            incident_id=inc_a.id, actor="DevOpsLead", command="ec2:RevokeSecurityGroupIngress", tool="MockSSMAdapter",
            target="sg-012345", reason="Revoke port 22 ingress and reset pool", idempotency_key=f"act-a3-{uuid.uuid4()}",
            result="SUCCESS", error_message=None, timestamp=start_a
        ))
        db.flush()

        text_a = "auth-service in us-east-1 experienced database connection exhaustion and high CPU. Revoking port 22 ingress successfully resolved."
        vec_a = provider.generate_embedding(text_a)
        db.add(InstitutionalMemoryVector(
            title="Incident A: Auth Service Connection Exhaustion", content=text_a, redacted_content=text_a,
            memory_type="remediation", entity_id="i-auth-ec2-01", incident_id=inc_a.id,
            evidence_references={"evidence_ids": [ev_a.id]}, embedding=vec_a, trust_level=TrustLevel.VERIFIED_GOLD
        ))

        # =====================================================================
        # INCIDENT B (Gold Rank 2 Candidate - Same service/symptom, different version)
        # =====================================================================
        start_b = datetime.fromisoformat("2026-08-16T18:00:00+00:00")
        inc_b = Incident(
            title="Database Connection Exhaustion & Auth Handshake Timeout",
            description="auth-service experienced connection pool timeout accessing CockroachDB cluster.",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.RESOLVED,
            service="auth-service",
            region="us-east-1",
            start_time=start_b,
            end_time=datetime.fromisoformat("2026-08-16T18:40:00+00:00"),
            target_resource_id="crdb-cluster-01",
            environment_fingerprint={"service": "auth-service", "region": "us-east-1"},
            root_cause_summary="Stale IAM authentication secret token caused DB handshake retry storm.",
            memory_status="COMPLETED"
        )
        db.add(inc_b)
        db.flush()

        raw_b = {"AlarmName": "DatabaseConnectionExhaustion", "StateValue": "ALARM", "Service": "auth-service"}
        hash_b = hashlib.sha256(json.dumps(raw_b, sort_keys=True).encode("utf-8")).hexdigest()
        ev_b = IncidentEvidence(
            incident_id=inc_b.id, source="cloudwatch", source_event_id="cw-inc-b",
            captured_at=start_b, event_type="database_connection_exhaustion",
            raw_payload=raw_b, content_hash=hash_b, trust_level=TrustLevel.MEDIUM
        )
        db.add(ev_b)

        db.add(InfrastructureSnapshot(
            incident_id=inc_b.id, snapshot_timestamp=start_b, db_version="CockroachDB v23.2.3",
            service_version="v4.1.0", topology={"service": "auth-service"}, configuration={"pool": 80},
            dependencies={"db": "crdb-cluster-01"}, resource_identifiers=["crdb-cluster-01"], region="us-east-1", traffic_info={}
        ))

        db.add(OperationalActionHistory(
            incident_id=inc_b.id, actor="GhostOps", command="cockroach:RestartClusterNode", tool="MockCockroachAdapter",
            target="crdb-cluster-01", reason="Cluster node restart attempt", idempotency_key=f"act-b1-{uuid.uuid4()}",
            result="FAILED", error_message="Cluster restart failed to fix stale secret.", timestamp=start_b
        ))
        db.add(OperationalActionHistory(
            incident_id=inc_b.id, actor="DevOpsLead", command="secretsmanager:RotateSecret", tool="MockSecretsManagerAdapter",
            target="arn:aws:secretsmanager:secret/db-auth", reason="Rotate DB auth IAM token secret", idempotency_key=f"act-b2-{uuid.uuid4()}",
            result="SUCCESS", error_message=None, timestamp=start_b
        ))
        db.flush()

        text_b = "auth-service in us-east-1 experienced database connection exhaustion. Rotating DB auth IAM token secret resolved connectivity."
        vec_b = provider.generate_embedding(text_b)
        db.add(InstitutionalMemoryVector(
            title="Incident B: Auth Service DB Connection Exhaustion", content=text_b, redacted_content=text_b,
            memory_type="remediation", entity_id="crdb-cluster-01", incident_id=inc_b.id,
            evidence_references={"evidence_ids": [ev_b.id]}, embedding=vec_b, trust_level=TrustLevel.HIGH
        ))

        # =====================================================================
        # INCIDENT C (Gold Rank 3 Candidate - Different service/DB version, failed action)
        # =====================================================================
        start_c = datetime.fromisoformat("2026-08-10T12:00:00+00:00")
        inc_c = Incident(
            title="Database Connection Timeout on Billing Service",
            description="billing-service experienced connection pool timeout accessing PostgreSQL database.",
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.CLOSED,
            service="billing-service",
            region="us-east-1",
            start_time=start_c,
            target_resource_id="postgres-db-01",
            environment_fingerprint={"service": "billing-service", "region": "us-east-1"},
            root_cause_summary="Unindexed query lock wait on billing records.",
            memory_status="COMPLETED"
        )
        db.add(inc_c)
        db.flush()

        raw_c = {"AlarmName": "DatabaseConnectionTimeout", "StateValue": "ALARM", "Service": "billing-service"}
        hash_c = hashlib.sha256(json.dumps(raw_c, sort_keys=True).encode("utf-8")).hexdigest()
        ev_c = IncidentEvidence(
            incident_id=inc_c.id, source="cloudwatch", source_event_id="cw-inc-c",
            captured_at=start_c, event_type="database_connection_timeout",
            raw_payload=raw_c, content_hash=hash_c, trust_level=TrustLevel.MEDIUM
        )
        db.add(ev_c)

        db.add(InfrastructureSnapshot(
            incident_id=inc_c.id, snapshot_timestamp=start_c, db_version="PostgreSQL v14.0",
            service_version="v3.0.0", topology={"service": "billing-service"}, configuration={"pool": 20},
            dependencies={"db": "postgres-db-01"}, resource_identifiers=["postgres-db-01"], region="us-east-1", traffic_info={}
        ))

        db.add(OperationalActionHistory(
            incident_id=inc_c.id, actor="GhostOps", command="ecs:RestartService", tool="MockECSAdapter",
            target="billing-service", reason="Restart billing container", idempotency_key=f"act-c1-{uuid.uuid4()}",
            result="FAILED", error_message="Restart failed; lock wait remains.", timestamp=start_c
        ))
        db.flush()

        text_c = "billing-service in us-east-1 experienced database connection timeout on PostgreSQL 14. Restarting container failed."
        vec_c = provider.generate_embedding(text_c)
        db.add(InstitutionalMemoryVector(
            title="Incident C: Billing Service DB Timeout", content=text_c, redacted_content=text_c,
            memory_type="symptom", entity_id="postgres-db-01", incident_id=inc_c.id,
            evidence_references={"evidence_ids": [ev_c.id]}, embedding=vec_c, trust_level=TrustLevel.MEDIUM
        ))

        # =====================================================================
        # INCIDENT D (Gold Rank 4 Candidate - Same service, completely different symptom)
        # =====================================================================
        start_d = datetime.fromisoformat("2026-08-01T09:00:00+00:00")
        inc_d = Incident(
            title="Unauthorized API Access Anomaly",
            description="auth-service detected unauthorized token issuance requests from untrusted IP block.",
            severity=IncidentSeverity.LOW,
            status=IncidentStatus.RESOLVED,
            service="auth-service",
            region="us-east-1",
            start_time=start_d,
            target_resource_id="auth-role-arn",
            environment_fingerprint={"service": "auth-service", "region": "us-east-1"},
            root_cause_summary="Stale IAM role policy scope.",
            memory_status="COMPLETED"
        )
        db.add(inc_d)
        db.flush()

        raw_d = {"AlarmName": "UnauthorizedAPICall", "StateValue": "ALARM", "Service": "auth-service"}
        hash_d = hashlib.sha256(json.dumps(raw_d, sort_keys=True).encode("utf-8")).hexdigest()
        ev_d = IncidentEvidence(
            incident_id=inc_d.id, source="cloudtrail", source_event_id="ct-inc-d",
            captured_at=start_d, event_type="unauthorized_api_call",
            raw_payload=raw_d, content_hash=hash_d, trust_level=TrustLevel.MEDIUM
        )
        db.add(ev_d)

        db.add(InfrastructureSnapshot(
            incident_id=inc_d.id, snapshot_timestamp=start_d, db_version="CockroachDB v23.2.3",
            service_version="v4.2.0", topology={"service": "auth-service"}, configuration={"pool": 50},
            dependencies={"iam": "auth-role-arn"}, resource_identifiers=["auth-role-arn"], region="us-east-1", traffic_info={}
        ))

        db.add(OperationalActionHistory(
            incident_id=inc_d.id, actor="DevOpsLead", command="iam:PutRolePolicy", tool="MockIAMAdapter",
            target="auth-role-arn", reason="Restrict role scope policy", idempotency_key=f"act-d1-{uuid.uuid4()}",
            result="SUCCESS", error_message=None, timestamp=start_d
        ))
        db.flush()

        text_d = "auth-service in us-east-1 experienced unauthorized API access anomaly. Restricting IAM role policy resolved access."
        vec_d = provider.generate_embedding(text_d)
        db.add(InstitutionalMemoryVector(
            title="Incident D: Auth Service Unauthorized API Access", content=text_d, redacted_content=text_d,
            memory_type="remediation", entity_id="auth-role-arn", incident_id=inc_d.id,
            evidence_references={"evidence_ids": [ev_d.id]}, embedding=vec_d, trust_level=TrustLevel.HIGH
        ))

        db.commit()
        print("Database successfully seeded with Golden Retrieval Dataset (Incidents A, B, C, D)!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
