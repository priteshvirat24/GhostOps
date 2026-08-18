import os
import sys
import uuid
import json
import hashlib
from datetime import datetime, timezone, timedelta

# Add apps/api and packages/shared to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "shared", "src")))

from sqlalchemy.orm import Session
from sqlalchemy import select, delete
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
from app.services.retrieval.historical_corpus import HistoricalCorpusRegistry, HistoricalMemoryRecord
from app.agents import get_model_provider
from app.core.redaction import redact_secrets

def seed_database(reseed: bool = False):
    print("Initializing CockroachDB tables...")
    Base.metadata.create_all(bind=engine)

    if "--init-only" in sys.argv:
        print("Schema initialized successfully!")
        return

    db: Session = SessionLocal()
    try:
        if "--reseed" in sys.argv or reseed:
            print("Cleaning obsolete/synthetic test-drift memories from database...")
            # Clean test-specific mirror records if present
            db.query(InstitutionalMemoryVector).filter(
                InstitutionalMemoryVector.id.like("mem-inc-drift-%")
            ).delete(synchronize_session=False)
            db.commit()

        corpus = HistoricalCorpusRegistry.get_corpus()
        print(f"Seeding GhostOps Independent Historical Memory Corpus ({HistoricalCorpusRegistry.CORPUS_VERSION}: {len(corpus)} records)...")
        provider = get_model_provider()
        now_time = datetime.now(timezone.utc)

        records_added = 0
        for rec in corpus:
            # 1. Ensure or create Incident record
            inc = db.get(Incident, rec.incident_id)
            inc_start = now_time - timedelta(days=rec.days_ago)
            if not inc:
                inc = Incident(
                    id=rec.incident_id,
                    title=rec.title,
                    description=rec.description,
                    severity=IncidentSeverity[rec.severity] if rec.severity in IncidentSeverity.__members__ else IncidentSeverity.HIGH,
                    status=IncidentStatus.RESOLVED,
                    service=rec.service,
                    region=rec.region,
                    start_time=inc_start,
                    end_time=inc_start + timedelta(minutes=45),
                    target_resource_id=f"{rec.service}-cluster",
                    environment_fingerprint={"service": rec.service, "region": rec.region},
                    root_cause_summary=rec.root_cause,
                    memory_status="COMPLETED"
                )
                db.add(inc)
                db.flush()

            # 2. Add Incident Evidence Item
            ev_id = f"ev-{rec.incident_id}-01"
            inc_ev = db.query(IncidentEvidence).filter(
                IncidentEvidence.incident_id == rec.incident_id
            ).first()
            if not inc_ev:
                raw_ev = {
                    "source": "CloudWatch",
                    "metric": "ErrorRate",
                    "symptoms": rec.symptoms,
                    "service": rec.service,
                    "region": rec.region
                }
                raw_hash = hashlib.sha256(json.dumps(raw_ev, sort_keys=True).encode("utf-8")).hexdigest()
                inc_ev = IncidentEvidence(
                    id=ev_id,
                    incident_id=rec.incident_id,
                    source="cloudwatch",
                    source_event_id=f"cw-{rec.incident_id}",
                    captured_at=inc_start,
                    event_type=rec.symptoms[0] if rec.symptoms else "telemetry_anomaly",
                    raw_payload=raw_ev,
                    content_hash=raw_hash,
                    trust_level=TrustLevel.HIGH
                )
                db.add(inc_ev)
                db.flush()

            # 3. Add Infrastructure Snapshot
            snap = db.query(InfrastructureSnapshot).filter(
                InfrastructureSnapshot.incident_id == rec.incident_id
            ).first()
            if not snap:
                snap = InfrastructureSnapshot(
                    incident_id=rec.incident_id,
                    snapshot_timestamp=inc_start,
                    db_version=rec.db_version,
                    service_version=rec.service_version,
                    topology=rec.topology,
                    configuration=rec.configuration,
                    dependencies={"db": "cockroach-cloud"},
                    resource_identifiers=[f"{rec.service}-host"],
                    region=rec.region,
                    traffic_info={}
                )
                db.add(snap)
                db.flush()

            # 4. Add Operational Action History
            act = db.query(OperationalActionHistory).filter(
                OperationalActionHistory.incident_id == rec.incident_id
            ).first()
            if not act:
                act = OperationalActionHistory(
                    incident_id=rec.incident_id,
                    actor="DevOpsLead",
                    command=rec.action_command,
                    tool="MockAWSAdapter",
                    target=f"{rec.service}-res",
                    reason=f"Remediation for {rec.title}",
                    idempotency_key=f"act-{rec.incident_id}-{uuid.uuid4().hex[:8]}",
                    result=rec.action_result,
                    error_message=None if rec.action_result == "SUCCESS" else "Action failed to restore service metrics.",
                    timestamp=inc_start + timedelta(minutes=15)
                )
                db.add(act)
                db.flush()

            # 5. Add Institutional Memory Vector with native VECTOR(1536) embedding
            mem_id = f"mem-{rec.incident_id}"
            mem_vec_obj = db.get(InstitutionalMemoryVector, mem_id)
            rich_text = rec.to_rich_content()
            emb = provider.generate_embedding(rich_text)

            trust_enum = TrustLevel.HIGH
            if rec.trust_level == "VERIFIED_GOLD":
                trust_enum = TrustLevel.VERIFIED_GOLD
            elif rec.trust_level == "LOW":
                trust_enum = TrustLevel.LOW
            elif rec.trust_level == "MEDIUM":
                trust_enum = TrustLevel.MEDIUM

            if not mem_vec_obj:
                mem_vec_obj = InstitutionalMemoryVector(
                    id=mem_id,
                    incident_id=rec.incident_id,
                    entity_id=rec.service,
                    title=rec.title,
                    content=rich_text,
                    redacted_content=redact_secrets(rich_text),
                    memory_type=rec.memory_type,
                    embedding=emb,
                    trust_level=trust_enum,
                    confidence=0.90 if rec.action_result == "SUCCESS" else 0.70,
                    memory_status=rec.memory_status,
                    superseded_by=rec.superseded_by,
                    created_at=inc_start,
                    evidence_references={"evidence_ids": [inc_ev.id]}
                )
                db.add(mem_vec_obj)
                records_added += 1
            else:
                # Update existing memory with rich content and embedding
                mem_vec_obj.content = rich_text
                mem_vec_obj.redacted_content = redact_secrets(rich_text)
                mem_vec_obj.embedding = emb
                mem_vec_obj.memory_type = rec.memory_type
                mem_vec_obj.trust_level = trust_enum
                mem_vec_obj.memory_status = rec.memory_status
                mem_vec_obj.superseded_by = rec.superseded_by

        db.commit()
        print(f"Database successfully populated with {len(corpus)} independent historical records ({records_added} new memories created)!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
