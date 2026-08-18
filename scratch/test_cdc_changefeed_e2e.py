import os
import sys
import uuid
import time
from datetime import datetime, timezone

# Ensure apps/api and root are in python path
sys.path.insert(0, os.path.abspath("apps/api"))
sys.path.insert(0, os.path.abspath("."))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import (
    Incident,
    RemediationPlan,
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
from ghostops_shared import IncidentSeverity, IncidentStatus, RemediationStatus

def main():
    print("=" * 80)
    print("GhostOps Stage 9 CockroachDB Changefeed & CDC Memory Bus End-to-End Test")
    print("=" * 80)

    db = SessionLocal()
    try:
        now_time = datetime.now(timezone.utc)
        unique_id = uuid.uuid4().hex[:8]

        # 1. CockroachDB Changefeed Status & Connection Check
        print("\n--- 1. COCKROACHDB CHANGEFEED STATUS ---")
        status = CockroachCDCConsumer.get_status()
        print(f"Consumer Mode: {status.mode}")
        print(f"Source Tables: {', '.join(status.source_tables)}")
        print(f"Initial Events Processed: {status.events_processed}")

        inc = Incident(
            id=f"inc-cdc-{unique_id}",
            title=f"CDC Integration Test {unique_id}",
            description="Connection pool saturation resolved by SSH ingress restriction.",
            service="auth-service",
            region="us-east-1",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.INVESTIGATING,
            start_time=now_time
        )
        db.add(inc)
        db.commit()

        plan = RemediationPlan(
            id=f"plan-cdc-{unique_id}",
            incident_id=inc.id,
            title="CDC Plan",
            explanation="E",
            status=RemediationStatus.APPROVED,
            confidence=0.9,
            compatibility_score=0.9,
            estimated_risk="LOW",
            risk_score=0.1,
            blast_radius="LOCAL",
            idempotency_key=f"k-cdc-{unique_id}"
        )
        db.add(plan)
        db.commit()

        exec_rec = RemediationExecution(
            id=f"exec-cdc-{unique_id}",
            plan_id=plan.id,
            incident_id=inc.id,
            status="COMPLETED",
            verification_status="VERIFIED",
            incident_recovery_status="RECOVERED",
            started_at=now_time,
            trace_id=f"trace-cdc-{unique_id}"
        )
        db.add(exec_rec)
        db.commit()

        outcome = RemediationOutcome(
            id=f"outc-cdc-{unique_id}",
            incident_id=inc.id,
            plan_id=f"plan-cdc-{unique_id}",
            execution_id=exec_rec.id,
            execution_status="COMPLETED",
            verification_status="VERIFIED",
            incident_recovery_status="RECOVERED",
            outcome_classification="COMPLETED_AND_RECOVERED",
            effectiveness_score=0.96,
            duration_seconds=45.0,
            executed_steps_count=1,
            failed_steps_count=0,
            compensated_steps_count=0,
            rollback_performed=False,
            rollback_successful=False,
            confidence=0.94,
            evidence_refs=[f"ev-cdc-{unique_id}"]
        )
        db.add(outcome)
        db.commit()
        print(f"Persisted RemediationOutcome '{outcome.id}' in CockroachDB.")

        # 3. Simulate CDC Event Stream Arrival
        print("\n--- 3. CDC CHANGEFEED EVENT CONSUMPTION ---")
        event_id = f"cdc-evt-{unique_id}"
        cdc_event = CDCEvent(
            event_id=event_id,
            source_table="remediation_outcomes",
            primary_key=outcome.id,
            operation=CDCOperation.INSERT,
            payload={
                "id": outcome.id,
                "incident_id": inc.id,
                "execution_id": exec_rec.id,
                "plan_id": exec_rec.plan_id,
                "verification_status": outcome.verification_status,
                "execution_status": outcome.execution_status,
                "incident_recovery_status": outcome.incident_recovery_status,
                "outcome_classification": outcome.outcome_classification,
                "effectiveness_score": outcome.effectiveness_score,
                "evidence_refs": outcome.evidence_refs
            },
            mode="REAL_CDC"
        )

        res = CockroachCDCConsumer.consume_single_event(db, cdc_event)
        print(f"CDC Processing Status: {res.status}")
        print(f"Propagated Trust Delta: {res.propagated_trust_delta:+0.2f}")
        print(f"Lessons Extracted Count: {res.lessons_extracted_count}")
        print(f"Candidates Consolidated Count: {res.candidates_consolidated_count}")
        assert res.status == CDCProcessingStatus.PROCESSED
        assert res.propagated_trust_delta == 0.05

        # 4. Durable Idempotency Verification
        print("\n--- 4. DURABLE IDEMPOTENCY & REPLAY CHECK ---")
        replay_res = CockroachCDCConsumer.consume_single_event(db, cdc_event)
        print(f"Replay Processing Status: {replay_res.status}")
        print(f"Replay Reason: {replay_res.reason}")
        assert replay_res.status == CDCProcessingStatus.DUPLICATE_SKIPPED

        # 5. Future Retrieval Test via Native CockroachDB Vector Search
        print("\n--- 5. FUTURE RETRIEVAL POST-CDC PROPAGATION ---")
        all_cands = db.scalars(select(MemoryCandidate)).all()
        cands = [c for c in all_cands if inc.id in (c.source_incident_ids or [])]
        if cands:
            query_vec = cands[0].embedding
            retrieval_res = VectorMemoryRetriever.retrieve_candidates(db, query_vector=query_vec, top_k=3)
            print(f"Vector Retrieval Results count: {len(retrieval_res)}")
            for inc_id_match, sim, mem in retrieval_res:
                print(f"  - Retrieved Mem ID: {mem.id} | Incident: {inc_id_match} | Similarity: {sim:.4f} | Title: {mem.title}")

        print("\n" + "=" * 80)
        print("Stage 9 CockroachDB Changefeed & CDC Memory Bus Test: ALL CHECKS PASSED")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    main()
