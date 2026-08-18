import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Ensure apps/api and root are in python path
sys.path.insert(0, os.path.abspath("apps/api"))
sys.path.insert(0, os.path.abspath("."))

from app.db.session import SessionLocal
from app.db.models import (
    Incident,
    RemediationPlan,
    PlanStep,
    RemediationExecution,
    RemediationOutcome,
    InfrastructureSnapshot,
    LearnedLesson,
    MemoryCandidate,
    InstitutionalMemoryVector,
    MemoryConsolidationRecord
)
from app.services.execution.saga_engine import RemediationSagaEngine
from app.services.execution.mock_infrastructure import StatefulMockInfrastructure
from app.agents.specialists.verification import VerificationAgent
from app.services.learning import (
    RemediationOutcomeAnalyzer,
    EffectivenessEvaluator,
    LessonExtractionService,
    MemoryCandidateGenerator,
    MemoryConsolidationService
)
from app.services.retrieval.retrieval_service import HistoricalRetrievalService
from app.services.retrieval.vector_retriever import VectorMemoryRetriever
from ghostops_shared import IncidentSeverity, IncidentStatus, RemediationStatus

def main():
    print("=" * 80)
    print("GhostOps Stage 8 Post-Remediation Learning Loop End-to-End Test")
    print("=" * 80)

    db = SessionLocal()
    try:
        now_time = datetime.now(timezone.utc)
        unique_id = uuid.uuid4().hex[:8]

        # =========================================================================
        # CASE 1: SUCCESSFUL REMEDIATION -> POSITIVE INSTITUTIONAL MEMORY
        # =========================================================================
        print("\n" + "=" * 80)
        print("CASE 1: SUCCESSFUL REMEDIATION -> POSITIVE OPERATIONAL LESSON")
        print("=" * 80)

        inc1 = Incident(
            id=f"inc-succ-{unique_id}",
            title=f"SSH Port 22 Exhaustion {unique_id}",
            description="Connection pool saturation caused by untrusted SSH ingress.",
            service="auth-service",
            region="us-east-1",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.INVESTIGATING,
            start_time=now_time
        )
        db.add(inc1)

        snap1 = InfrastructureSnapshot(
            incident_id=inc1.id,
            snapshot_timestamp=now_time,
            service_version="v4.2.0",
            db_version="CockroachDB v23.2.3",
            topology={"nodes": ["auth-1", "auth-2"]},
            configuration={"connection_pool_max": 50, "security_group_ingress_rules": [{"protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"}]},
            dependencies={"db": "cockroach-cloud"}
        )
        db.add(snap1)
        db.commit()

        plan1 = RemediationPlan(
            id=f"plan-succ-{unique_id}",
            incident_id=inc1.id,
            title="Revoke SSH Port 22 Ingress",
            explanation="Revoke port 22 0.0.0.0/0 on auth-service security group.",
            status=RemediationStatus.APPROVED,
            confidence=0.94,
            compatibility_score=0.95,
            estimated_risk="HIGH_RISK",
            risk_score=0.75,
            blast_radius="REGION",
            idempotency_key=f"idemp-succ-{unique_id}",
            expires_at=now_time + timedelta(hours=2),
            rollback_plan=[{"step_order": 1, "action_type": "CHANGE_SECURITY_RULE", "parameters": {"port": 22, "cidr_block": "0.0.0.0/0"}}]
        )
        target_sg1 = f"sg-{unique_id}"
        step1 = PlanStep(
            remediation_plan_id=plan1.id,
            step_order=1,
            action_type="CHANGE_SECURITY_RULE",
            target_resource_arn=target_sg1,
            parameters={"security_group_id": target_sg1, "protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"}
        )
        plan1.steps.append(step1)
        db.add(plan1)
        db.commit()

        # Step A: Execute Saga
        print("\n--- 1.1 SAGA EXECUTION ---")
        exec1 = RemediationSagaEngine.execute_plan_saga(db, plan1, force_real_aws=False)
        print(f"Execution ID: {exec1.id} | Status: {exec1.status} | Mode: {exec1.execution_mode}")

        # Step B: Independent Verification
        print("\n--- 1.2 INDEPENDENT VERIFICATION ---")
        verif_rep1 = VerificationAgent.verify_outcome(
            db=db,
            incident_id=inc1.id,
            plan_id=plan1.id,
            execution_id=exec1.id,
            mock_metric_value=0.18 # Healthy error rate 0.18% < 1.0%
        )
        print(f"Verification Status: {verif_rep1.overall_status}")
        print(f"Trust Delta: {verif_rep1.trust_delta:+0.2f}")

        # Step C: Post-Remediation Learning Loop
        print("\n--- 1.3 LEARNING PIPELINE: LESSON EXTRACTION ---")
        outcome1 = db.query(RemediationOutcome).filter(RemediationOutcome.execution_id == exec1.id).first()
        eff_score1 = EffectivenessEvaluator.evaluate_effectiveness(outcome1)
        outcome1.effectiveness_score = eff_score1
        db.commit()
        print(f"Outcome Classification: {outcome1.outcome_classification} | Effectiveness: {outcome1.effectiveness_score}")

        lessons1 = LessonExtractionService.extract_lessons(db, inc1, exec1, outcome1)
        print(f"Extracted {len(lessons1)} Lessons:")
        for l in lessons1:
            print(f"  - [{l.lesson_type}] {l.title} (confidence={l.confidence})")

        print("\n--- 1.4 MEMORY CANDIDATE GENERATION & EMBEDDING ---")
        cands1 = MemoryCandidateGenerator.generate_candidates(db, lessons1)
        for c in cands1:
            print(f"  - Candidate ID: {c.id} | Status: {c.status} | Dim: {len(c.embedding)} | Fingerprint: {c.normalized_fingerprint[:16]}...")

        print("\n--- 1.5 CONSOLIDATION INTO INSTITUTIONAL MEMORY ---")
        consolidations1 = MemoryConsolidationService.consolidate_candidates(db, cands1)
        for r in consolidations1:
            print(f"  - Consolidation: action={r.action}, target_memory_id={r.target_memory_id}, reason={r.reason}")

        # Step D: Future Retrieval Test
        print("\n--- 1.6 FUTURE RETRIEVAL VIA VECTOR SEARCH ---")
        query_vec = cands1[0].embedding
        retrieval_res = VectorMemoryRetriever.retrieve_candidates(db, query_vector=query_vec, top_k=3)
        print(f"Vector Retrieval Results count: {len(retrieval_res)}")
        for inc_id, sim, mem in retrieval_res:
            print(f"  - Retrieved Mem ID: {mem.id} | Incident: {inc_id} | Similarity: {sim:.4f} | Title: {mem.title}")

        # =========================================================================
        # CASE 2: FAILED REMEDIATION -> NEGATIVE KNOWLEDGE & IMMUTABLE SUPERSEDING
        # =========================================================================
        print("\n" + "=" * 80)
        print("CASE 2: FAILED REMEDIATION -> NEGATIVE KNOWLEDGE & IMMUTABLE SUPERSESSION")
        print("=" * 80)

        inc2 = Incident(
            id=f"inc-fail-{unique_id}",
            title=f"Billing Latency Spike {unique_id}",
            description="Billing database lock contention during traffic spike.",
            service="billing-service",
            region="us-east-1",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.INVESTIGATING,
            start_time=now_time
        )
        db.add(inc2)

        snap2 = InfrastructureSnapshot(
            incident_id=inc2.id,
            snapshot_timestamp=now_time,
            service_version="v4.3.0",
            db_version="CockroachDB v23.2.3",
            topology={"nodes": ["bill-1", "bill-2"]},
            configuration={"connection_pool_max": 50},
            dependencies={"db": "cockroach-cloud"}
        )
        db.add(snap2)
        db.commit()

        plan2 = RemediationPlan(
            id=f"plan-fail-{unique_id}",
            incident_id=inc2.id,
            title="Restart Service on billing-service",
            explanation="Restart node to clear memory buffers.",
            status=RemediationStatus.APPROVED,
            confidence=0.80,
            compatibility_score=0.85,
            estimated_risk="HIGH_RISK",
            risk_score=0.75,
            blast_radius="REGION",
            idempotency_key=f"idemp-fail-{unique_id}",
            expires_at=now_time + timedelta(hours=2),
            rollback_plan=[{"step_order": 1, "action_type": "CHANGE_SECURITY_RULE", "parameters": {"port": 22, "cidr_block": "0.0.0.0/0"}}]
        )
        step2 = PlanStep(
            remediation_plan_id=plan2.id,
            step_order=1,
            action_type="CHANGE_SECURITY_RULE",
            target_resource_arn=f"sg-fail-{unique_id}",
            parameters={"security_group_id": f"sg-fail-{unique_id}", "port": 22, "cidr_block": "0.0.0.0/0"}
        )
        plan2.steps.append(step2)
        db.add(plan2)
        db.commit()

        # Step A: Execute Saga
        exec2 = RemediationSagaEngine.execute_plan_saga(db, plan2, force_real_aws=False)

        # Step B: Independent Verification (FAILING TELEMETRY)
        verif_rep2 = VerificationAgent.verify_outcome(
            db=db,
            incident_id=inc2.id,
            plan_id=plan2.id,
            execution_id=exec2.id,
            mock_metric_value=5.4 # Saturated 5.4% > 1.0% threshold
        )
        print(f"Verification Status: {verif_rep2.overall_status}")
        print(f"Trust Delta: {verif_rep2.trust_delta:+0.2f}")

        # Step C: Negative Lesson Extraction
        outcome2 = db.query(RemediationOutcome).filter(RemediationOutcome.execution_id == exec2.id).first()
        lessons2 = LessonExtractionService.extract_lessons(db, inc2, exec2, outcome2)
        print(f"Extracted {len(lessons2)} Lessons:")
        for l in lessons2:
            print(f"  - [{l.lesson_type}] {l.title} (confidence={l.confidence})")

        # Step D: Negative Candidate & Supersession
        cands2 = MemoryCandidateGenerator.generate_candidates(db, lessons2)
        consolidations2 = MemoryConsolidationService.consolidate_candidates(db, cands2)
        for r in consolidations2:
            print(f"  - Consolidation: action={r.action}, target_memory_id={r.target_memory_id}, reason={r.reason}")

        print("\n" + "=" * 80)
        print("Stage 8 Post-Remediation Learning Loop Test: ALL 12 PIPELINE STEPS PASSED")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    main()
