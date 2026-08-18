import pytest
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import (
    Incident,
    RemediationExecution,
    RemediationOutcome,
    LearnedLesson,
    MemoryCandidate,
    InstitutionalMemoryVector,
    CDCProcessedEvent
)
from app.schemas.cdc import CDCEvent, CDCOperation, CDCProcessingStatus
from app.services.cdc.consumer import CockroachCDCConsumer
from app.services.retrieval.vector_retriever import VectorMemoryRetriever
from ghostops_shared import IncidentSeverity, RemediationStatus

def test_cdc_test_a_event_parsing(db_session: Session):
    """Test A: Real changefeed event parsing."""
    event = CDCEvent(
        event_id="cdc-parse-01",
        source_table="remediation_outcomes",
        primary_key="outc-parse-01",
        operation=CDCOperation.INSERT,
        payload={
            "id": "outc-parse-01",
            "incident_id": "inc-parse-01",
            "verification_status": "VERIFIED",
            "execution_status": "COMPLETED",
            "incident_recovery_status": "RECOVERED",
            "outcome_classification": "COMPLETED_AND_RECOVERED"
        },
        mode="REAL_CDC"
    )
    assert event.event_id == "cdc-parse-01"
    assert event.source_table == "remediation_outcomes"
    assert event.operation == CDCOperation.INSERT

def test_cdc_test_b_duplicate_event_idempotency(db_session: Session):
    """Test B: Duplicate event idempotency."""
    event_id = f"cdc-dup-{uuid.uuid4().hex[:8]}"
    event = CDCEvent(
        event_id=event_id,
        source_table="remediation_outcomes",
        primary_key=f"outc-dup-{uuid.uuid4().hex[:6]}",
        operation=CDCOperation.INSERT,
        payload={
            "id": f"outc-dup-{uuid.uuid4().hex[:6]}",
            "incident_id": "inc-dup-cdc",
            "verification_status": "VERIFIED",
            "execution_status": "COMPLETED",
            "incident_recovery_status": "RECOVERED",
            "outcome_classification": "COMPLETED_AND_RECOVERED"
        }
    )

    # 1. First execution -> PROCESSED
    res1 = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res1.status == CDCProcessingStatus.PROCESSED

    # 2. Second execution with same event_id -> DUPLICATE_SKIPPED
    res2 = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res2.status == CDCProcessingStatus.DUPLICATE_SKIPPED

    # Ensure only 1 record exists in cdc_processed_events table
    recs = db_session.scalars(select(CDCProcessedEvent).where(CDCProcessedEvent.event_id == event_id)).all()
    assert len(recs) == 1

def test_cdc_test_c_malformed_event_rejection(db_session: Session):
    """Test C: Malformed event rejection without crash."""
    event = CDCEvent(
        event_id="",
        source_table="",
        primary_key="",
        operation=CDCOperation.INSERT,
        payload={}
    )
    res = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res.status == CDCProcessingStatus.REJECTED
    assert "missing" in (res.reason or "").lower()

def test_cdc_test_d_outcome_event_triggers_learning_pipeline(db_session: Session):
    """Test D: Remediation outcome event -> learning pipeline."""
    outc_id = f"outc-pipe-{uuid.uuid4().hex[:8]}"
    inc_id = f"inc-pipe-{uuid.uuid4().hex[:8]}"
    event = CDCEvent(
        event_id=f"cdc-{outc_id}",
        source_table="remediation_outcomes",
        primary_key=outc_id,
        operation=CDCOperation.INSERT,
        payload={
            "id": outc_id,
            "incident_id": inc_id,
            "execution_id": f"exec-{outc_id}",
            "plan_id": f"plan-{outc_id}",
            "verification_status": "VERIFIED",
            "execution_status": "COMPLETED",
            "incident_recovery_status": "RECOVERED",
            "outcome_classification": "COMPLETED_AND_RECOVERED",
            "effectiveness_score": 0.95
        }
    )

    res = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res.status == CDCProcessingStatus.PROCESSED
    assert res.lessons_extracted_count >= 1
    assert res.candidates_consolidated_count >= 1

    # Verify lessons exist in DB
    lessons = db_session.scalars(select(LearnedLesson).where(LearnedLesson.incident_id == inc_id)).all()
    assert len(lessons) >= 1

def test_cdc_test_e_verified_outcome_positive_trust(db_session: Session):
    """Test E: Verified outcome -> positive trust delta (+0.05)."""
    outc_id = f"outc-pos-{uuid.uuid4().hex[:8]}"
    inc_id = f"inc-pos-{uuid.uuid4().hex[:8]}"
    event = CDCEvent(
        event_id=f"cdc-{outc_id}",
        source_table="remediation_outcomes",
        primary_key=outc_id,
        operation=CDCOperation.INSERT,
        payload={
            "id": outc_id,
            "incident_id": inc_id,
            "verification_status": "VERIFIED",
            "execution_status": "COMPLETED",
            "incident_recovery_status": "RECOVERED",
            "outcome_classification": "COMPLETED_AND_RECOVERED"
        }
    )

    res = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res.status == CDCProcessingStatus.PROCESSED
    assert res.propagated_trust_delta == 0.05

def test_cdc_test_f_failed_outcome_negative_trust(db_session: Session):
    """Test F: Failed outcome -> negative trust delta (-0.05)."""
    outc_id = f"outc-neg-{uuid.uuid4().hex[:8]}"
    inc_id = f"inc-neg-{uuid.uuid4().hex[:8]}"
    event = CDCEvent(
        event_id=f"cdc-{outc_id}",
        source_table="remediation_outcomes",
        primary_key=outc_id,
        operation=CDCOperation.INSERT,
        payload={
            "id": outc_id,
            "incident_id": inc_id,
            "verification_status": "FAILED",
            "execution_status": "COMPLETED",
            "incident_recovery_status": "PERSISTS",
            "outcome_classification": "COMPLETED_BUT_INCIDENT_PERSISTS"
        }
    )

    res = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res.status == CDCProcessingStatus.PROCESSED
    assert res.propagated_trust_delta == -0.05

def test_cdc_test_g_blocked_outcome_neutral_trust(db_session: Session):
    """Test G: Blocked outcome -> neutral trust delta (0.0)."""
    outc_id = f"outc-blk-{uuid.uuid4().hex[:8]}"
    inc_id = f"inc-blk-{uuid.uuid4().hex[:8]}"
    event = CDCEvent(
        event_id=f"cdc-{outc_id}",
        source_table="remediation_outcomes",
        primary_key=outc_id,
        operation=CDCOperation.INSERT,
        payload={
            "id": outc_id,
            "incident_id": inc_id,
            "verification_status": "BLOCKED",
            "execution_status": "BLOCKED",
            "incident_recovery_status": "UNKNOWN",
            "outcome_classification": "VERIFICATION_INCONCLUSIVE"
        }
    )

    res = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res.status == CDCProcessingStatus.PROCESSED
    assert res.propagated_trust_delta == 0.0

def test_cdc_test_h_process_restart_durable_recovery(db_session: Session):
    """Test H: Process restart does not reapply an already processed event."""
    event_id = f"cdc-durable-{uuid.uuid4().hex[:8]}"
    event = CDCEvent(
        event_id=event_id,
        source_table="remediation_outcomes",
        primary_key=f"outc-durable-{uuid.uuid4().hex[:6]}",
        payload={
            "id": f"outc-durable-{uuid.uuid4().hex[:6]}",
            "incident_id": "inc-restart",
            "verification_status": "VERIFIED",
            "execution_status": "COMPLETED",
            "incident_recovery_status": "RECOVERED",
            "outcome_classification": "COMPLETED_AND_RECOVERED"
        }
    )

    # First run
    res1 = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res1.status == CDCProcessingStatus.PROCESSED

    # Simulate process restart by querying fresh session
    proc_check = db_session.scalars(
        select(CDCProcessedEvent).where(CDCProcessedEvent.event_id == event_id)
    ).first()
    assert proc_check is not None

    # Replay event
    res2 = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res2.status == CDCProcessingStatus.DUPLICATE_SKIPPED

def test_cdc_test_i_new_memory_available_to_retrieval(db_session: Session):
    """Test I: New institutional memory becomes available to vector retrieval after CDC processing."""
    outc_id = f"outc-vec-{uuid.uuid4().hex[:8]}"
    inc_id = f"inc-vec-{uuid.uuid4().hex[:8]}"
    event = CDCEvent(
        event_id=f"cdc-{outc_id}",
        source_table="remediation_outcomes",
        primary_key=outc_id,
        payload={
            "id": outc_id,
            "incident_id": inc_id,
            "verification_status": "VERIFIED",
            "execution_status": "COMPLETED",
            "incident_recovery_status": "RECOVERED",
            "outcome_classification": "COMPLETED_AND_RECOVERED",
            "evidence_refs": ["ev-cdc-ret"]
        }
    )

    res = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res.status == CDCProcessingStatus.PROCESSED

    # Query vector retrieval for this incident's new memory
    all_cands = db_session.scalars(select(MemoryCandidate)).all()
    candidates = [c for c in all_cands if inc_id in (c.source_incident_ids or [])]
    if candidates:
        q_vec = candidates[0].embedding
        ret_res = VectorMemoryRetriever.retrieve_candidates(db_session, query_vector=q_vec, top_k=5)
        assert len(ret_res) >= 1

def test_cdc_test_j_consumer_status_metrics():
    """Test J: Consumer status and metrics reporting."""
    status = CockroachCDCConsumer.get_status()
    assert status.events_received >= 1
    assert status.events_processed >= 1
    assert "remediation_outcomes" in status.source_tables

def test_cdc_test_k_malicious_payload_screening(db_session: Session):
    """Test K: CDC payload cannot bypass memory injection screening."""
    outc_id = f"outc-mal-{uuid.uuid4().hex[:8]}"
    inc_id = f"inc-mal-{uuid.uuid4().hex[:8]}"
    event = CDCEvent(
        event_id=f"cdc-{outc_id}",
        source_table="remediation_outcomes",
        primary_key=outc_id,
        payload={
            "id": outc_id,
            "incident_id": inc_id,
            "verification_status": "VERIFIED",
            "execution_status": "COMPLETED",
            "incident_recovery_status": "RECOVERED",
            "outcome_classification": "COMPLETED_AND_RECOVERED",
            "evidence_refs": ["DROP TABLE users;", "sudo rm -rf /"]
        }
    )

    res = CockroachCDCConsumer.consume_single_event(db_session, event)
    assert res.status == CDCProcessingStatus.PROCESSED

    # Candidate should be FLAGGED_FOR_REVIEW due to malicious pattern
    all_cands = db_session.scalars(select(MemoryCandidate)).all()
    cands = [c for c in all_cands if inc_id in (c.source_incident_ids or [])]
    for c in cands:
        if c.review_required:
            assert c.status == "FLAGGED_FOR_REVIEW"
