import json
import hashlib
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from ghostops_shared import IncidentSeverity, IncidentStatus, TrustLevel
from app.db.models import (
    Incident,
    IncidentEvent,
    IncidentEvidence,
    InfrastructureSnapshot,
    OperationalActionHistory,
    InstitutionalMemoryVector,
)
from app.schemas.normalized_event import NormalizedOperationalEvent, IngestionResultResponse
from app.services.normalizer import EventNormalizer
from app.core.redaction import redact_secrets
from app.agents import get_model_provider
from app.integrations.aws import MockAWSConfigAdapter
from app.core.logging import logger

class IncidentIngestionService:
    """
    Transactional Incident Ingestion Service for GhostOps Stage 2.
    Executes the 11-stage operational memory pipeline cleanly.
    """

    @staticmethod
    def ingest_operational_events(
        db: Session,
        raw_events: List[Dict[str, Any]],
        target_service: Optional[str] = None,
        region: Optional[str] = "us-east-1",
        actions_data: Optional[List[Dict[str, Any]]] = None,
        provided_root_cause: Optional[str] = None
    ) -> IngestionResultResponse:
        start_time_ms = time.time()
        logger.info(f"[IngestionService] Starting ingestion of {len(raw_events)} raw events")

        if not raw_events:
            raise ValueError("Ingestion payload must contain at least one operational event.")

        # 1. Normalize events deterministically
        normalized_events: List[NormalizedOperationalEvent] = [
            EventNormalizer.normalize_event(e) for e in raw_events
        ]

        # Sort chronologically by timestamp
        normalized_events.sort(key=lambda x: (x.timestamp, x.source, x.event_id))

        # Determine primary incident attributes from telemetry
        primary_evt = normalized_events[0]
        svc_name = target_service or primary_evt.service or "web-service"
        reg_name = region or primary_evt.region or "us-east-1"
        max_severity = max(e.severity for e in normalized_events)
        target_res = primary_evt.resource_id

        # 2. Check for duplicate source events and calculate content hashes
        unique_events: List[Tuple[NormalizedOperationalEvent, str, str]] = []
        duplicate_count = 0

        for norm_evt in normalized_events:
            json_str = json.dumps(norm_evt.raw_payload, sort_keys=True, default=str)
            content_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
            source_event_id = norm_evt.event_id

            # Check DB for existing evidence with same source & source_event_id
            existing = db.scalars(
                select(IncidentEvidence).where(
                    IncidentEvidence.source == norm_evt.source,
                    IncidentEvidence.source_event_id == source_event_id
                )
            ).first()

            if existing:
                duplicate_count += 1
            else:
                unique_events.append((norm_evt, source_event_id, content_hash))

        events_received = len(raw_events)
        events_created = len(unique_events)

        # 3. Create Incident DB Record inside database transaction
        fingerprint = {
            "service": svc_name,
            "region": reg_name,
            "event_sources": list(set(e.source for e in normalized_events)),
            "resource_ids": list(set(e.resource_id for e in normalized_events)),
        }

        incident = Incident(
            title=f"Telemetry Alert: {primary_evt.message[:80]}",
            description=f"Incident generated from {events_created} normalized operational events affecting {svc_name} in {reg_name}.",
            severity=max_severity,
            status=IncidentStatus.INVESTIGATING,
            service=svc_name,
            region=reg_name,
            start_time=primary_evt.timestamp,
            target_resource_id=target_res,
            environment_fingerprint=fingerprint,
            root_cause_summary=provided_root_cause, # Left NULL if not explicitly provided
            memory_status="COMPLETED"
        )
        db.add(incident)
        db.flush()

        # 4. Persist Raw Evidence records (Append-only)
        evidence_records: List[IncidentEvidence] = []
        for norm_evt, src_id, c_hash in unique_events:
            ev = IncidentEvidence(
                incident_id=incident.id,
                source=norm_evt.source,
                source_event_id=src_id,
                captured_at=norm_evt.timestamp,
                event_type=norm_evt.event_type,
                raw_payload=norm_evt.raw_payload,
                content_hash=c_hash,
                trust_level=TrustLevel.MEDIUM
            )
            db.add(ev)
            evidence_records.append(ev)

            # Also store as IncidentEvent for timeline
            inc_evt = IncidentEvent(
                incident_id=incident.id,
                event_source=norm_evt.source,
                event_name=norm_evt.event_type,
                event_timestamp=norm_evt.timestamp,
                payload=norm_evt.raw_payload
            )
            db.add(inc_evt)

        db.flush()

        # 5. Capture Immutable Infrastructure Snapshot
        config_adapter = MockAWSConfigAdapter()
        discovered = config_adapter.list_discovered_resources()
        snapshot = InfrastructureSnapshot(
            incident_id=incident.id,
            snapshot_timestamp=datetime.now(timezone.utc),
            db_version="CockroachDB v23.2.3",
            service_version="v2.1.0",
            topology={"nodes": discovered, "region": reg_name},
            configuration={"connection_pool": 50, "max_connections": 100},
            dependencies={"upstream": ["alb-public"], "downstream": ["cockroachdb-cluster"]},
            resource_identifiers=[e[0].resource_id for e in unique_events],
            region=reg_name,
            traffic_info={"requests_per_sec": 1450, "error_rate": 0.12}
        )
        db.add(snapshot)

        # 6. Persist Operational Actions (Preserving FAILED attempts & enforcing idempotency)
        if actions_data:
            for idx, act in enumerate(actions_data, start=1):
                idempotency_key = act.get("idempotency_key") or f"act-{incident.id}-{act.get('command')}-{idx}"
                action_record = OperationalActionHistory(
                    incident_id=incident.id,
                    saga_id=act.get("saga_id"),
                    actor=act.get("actor", "GhostOps.Orchestrator"),
                    agent=act.get("agent", "RemediationEngine"),
                    command=act.get("command", "ssm:RunCommand"),
                    tool=act.get("tool", "MockSSMAdapter"),
                    target=act.get("target", target_res),
                    risk_level=act.get("risk_level", "LOW"),
                    reason=act.get("reason", "Operational remediation attempt"),
                    authorization=act.get("authorization", "SystemAutoApproved"),
                    idempotency_key=idempotency_key,
                    result=act.get("result", "FAILED"),
                    error_message=act.get("error_message"),
                    timestamp=act.get("timestamp") or datetime.now(timezone.utc)
                )
                db.add(action_record)

        db.commit()

        # 7. Generate Operational Memory Records & Vector Embeddings
        memory_records_created = 0
        embedding_records_created = 0

        try:
            provider = get_model_provider()
            evidence_ids = [ev.id for ev in evidence_records]

            # Memory item 1: Symptom
            symptom_raw = f"Service {svc_name} in {reg_name} experienced {primary_evt.message}."
            symptom_redacted = redact_secrets(symptom_raw)
            vec1 = provider.generate_embedding(symptom_redacted)

            mem1 = InstitutionalMemoryVector(
                title=f"Symptom: {svc_name} telemetry spike",
                content=symptom_raw,
                redacted_content=symptom_redacted,
                memory_type="symptom",
                entity_id=target_res,
                incident_id=incident.id,
                evidence_references={"evidence_ids": evidence_ids},
                embedding=vec1,
                trust_level=TrustLevel.MEDIUM
            )
            db.add(mem1)
            memory_records_created += 1
            embedding_records_created += 1

            # Memory item 2: Timeline
            timeline_summary = f"Timeline reconstructed across {events_created} events starting at {primary_evt.timestamp.isoformat()}."
            timeline_redacted = redact_secrets(timeline_summary)
            vec2 = provider.generate_embedding(timeline_redacted)

            mem2 = InstitutionalMemoryVector(
                title=f"Timeline: {svc_name} event sequence",
                content=timeline_summary,
                redacted_content=timeline_redacted,
                memory_type="timeline",
                entity_id=target_res,
                incident_id=incident.id,
                evidence_references={"evidence_ids": evidence_ids},
                embedding=vec2,
                trust_level=TrustLevel.MEDIUM
            )
            db.add(mem2)
            memory_records_created += 1
            embedding_records_created += 1

            # Memory item 3: Remediation history (if actions existed)
            if actions_data:
                failed_acts = [a.get("command") for a in actions_data if a.get("result") == "FAILED"]
                success_acts = [a.get("command") for a in actions_data if a.get("result") == "SUCCESS"]
                rem_summary = f"Attempted actions: Failed={failed_acts}, Succeeded={success_acts}."
                rem_redacted = redact_secrets(rem_summary)
                vec3 = provider.generate_embedding(rem_redacted)

                mem3 = InstitutionalMemoryVector(
                    title=f"Remediation History: {svc_name}",
                    content=rem_summary,
                    redacted_content=rem_redacted,
                    memory_type="remediation",
                    entity_id=target_res,
                    incident_id=incident.id,
                    evidence_references={"evidence_ids": evidence_ids},
                    embedding=vec3,
                    trust_level=TrustLevel.HIGH
                )
                db.add(mem3)
                memory_records_created += 1
                embedding_records_created += 1

            # Memory item 4: Root Cause (ONLY if explicitly provided)
            if provided_root_cause:
                rc_redacted = redact_secrets(provided_root_cause)
                vec4 = provider.generate_embedding(rc_redacted)

                mem4 = InstitutionalMemoryVector(
                    title=f"Root Cause: {svc_name}",
                    content=provided_root_cause,
                    redacted_content=rc_redacted,
                    memory_type="root_cause",
                    entity_id=target_res,
                    incident_id=incident.id,
                    evidence_references={"evidence_ids": evidence_ids},
                    embedding=vec4,
                    trust_level=TrustLevel.VERIFIED_GOLD
                )
                db.add(mem4)
                memory_records_created += 1
                embedding_records_created += 1

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"Embedding generation failed during ingestion: {e}")
            incident.memory_status = "MEMORY_DEGRADED"
            db.commit()

        elapsed_ms = int((time.time() - start_time_ms) * 1000)
        logger.info(
            f"[IngestionService] Completed ingestion for {incident.id}: "
            f"received={events_received}, created={events_created}, duplicates={duplicate_count}, "
            f"memories={memory_records_created}, status={incident.memory_status}, duration={elapsed_ms}ms"
        )

        return IngestionResultResponse(
            incident_id=incident.id,
            status=incident.memory_status,
            events_received=events_received,
            events_created=events_created,
            duplicate_events=duplicate_count,
            memory_records_created=memory_records_created,
            embedding_records_created=embedding_records_created,
            execution_time_ms=elapsed_ms
        )
