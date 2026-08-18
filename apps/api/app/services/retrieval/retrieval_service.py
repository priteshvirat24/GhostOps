from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, asc

from app.db.models import (
    Incident,
    InfrastructureSnapshot,
    OperationalActionHistory,
    InstitutionalMemoryVector,
    IncidentEvidence,
)
from app.services.retrieval.fingerprint import IncidentFingerprint
from app.services.retrieval.structured_retriever import StructuredMemoryRetriever
from app.services.retrieval.vector_retriever import VectorMemoryRetriever
from app.services.retrieval.staleness import StalenessCalculator
from app.services.retrieval.scorer import HybridScorer
from app.agents import get_model_provider
from app.schemas.retrieval import HistoricalMemoryCandidateResponse, SimilarIncidentsResponse
from app.core.logging import logger

class HistoricalRetrievalService:
    """
    Historical Retrieval Engine Service for GhostOps Stage 3.
    Orchestrates fingerprinting, structured SQL candidates, CockroachDB vector candidates,
    candidate union, deduplication, outcome scoring, staleness penalties, and explainable ranking.
    """

    @staticmethod
    def get_similar_incidents(
        db: Session,
        incident_id: str,
        limit: int = 5,
        min_score: float = 0.0,
        include_failed_actions: bool = True
    ) -> SimilarIncidentsResponse:
        target_inc = db.get(Incident, incident_id)
        if not target_inc:
            raise ValueError(f"Target incident '{incident_id}' not found.")

        target_snap = db.scalars(
            select(InfrastructureSnapshot).where(InfrastructureSnapshot.incident_id == incident_id)
        ).first()
        target_evidence = db.scalars(
            select(IncidentEvidence).where(IncidentEvidence.incident_id == incident_id)
        ).all()

        # 1. Build Incident Fingerprint
        fingerprint = IncidentFingerprint.from_incident(target_inc, target_snap, target_evidence)
        canonical_text = fingerprint.to_canonical_text()

        # 2. Generate embedding for query text
        provider = get_model_provider()
        query_vector = provider.generate_embedding(canonical_text)

        # 3. Retrieve Structured candidates & Vector candidates
        struct_candidates = StructuredMemoryRetriever.retrieve_candidates(
            db, fingerprint, exclude_incident_id=incident_id
        )
        vector_candidates = VectorMemoryRetriever.retrieve_candidates(
            db, query_vector, memory_type=None
        )

        # 4. Candidate Union & Deduplication by incident_id
        candidate_map: Dict[str, Dict[str, Any]] = {}

        for inc_obj, struct_score, matched_fields in struct_candidates:
            if inc_obj.id == incident_id:
                continue
            candidate_map[inc_obj.id] = {
                "incident": inc_obj,
                "structured_score": struct_score,
                "semantic_score": 0.0,
                "matched_fields": matched_fields,
            }

        for vec_inc_id, sem_score, mem_obj in vector_candidates:
            if vec_inc_id == incident_id:
                continue
            if vec_inc_id in candidate_map:
                # Update max semantic score
                candidate_map[vec_inc_id]["semantic_score"] = max(
                    candidate_map[vec_inc_id]["semantic_score"], sem_score
                )
            else:
                inc_obj = db.get(Incident, vec_inc_id)
                if inc_obj:
                    # Build matched_fields for vector-only candidate
                    cand_snap = db.scalars(
                        select(InfrastructureSnapshot).where(InfrastructureSnapshot.incident_id == vec_inc_id)
                    ).first()
                    cand_ev = db.scalars(
                        select(IncidentEvidence).where(IncidentEvidence.incident_id == vec_inc_id)
                    ).all()
                    cand_fp = IncidentFingerprint.from_incident(inc_obj, cand_snap, cand_ev)
                    matched_fields = {
                        "service": cand_fp.service == fingerprint.service,
                        "region": cand_fp.region == fingerprint.region,
                        "symptom": bool(set(cand_fp.symptoms) & set(fingerprint.symptoms)),
                        "resource_type": bool(set(cand_fp.resource_types) & set(fingerprint.resource_types)),
                        "db_version": cand_fp.db_version == fingerprint.db_version,
                        "service_version": cand_fp.service_version == fingerprint.service_version,
                    }
                    candidate_map[vec_inc_id] = {
                        "incident": inc_obj,
                        "structured_score": 0.2, # Baseline structured score for vector match
                        "semantic_score": sem_score,
                        "matched_fields": matched_fields,
                    }

        # 5. Score & Rank Candidates
        scored_candidates: List[Dict[str, Any]] = []

        for cand_id, entry in candidate_map.items():
            inc_obj: Incident = entry["incident"]
            struct_score: float = entry["structured_score"]
            sem_score: float = entry["semantic_score"]
            matched_fields: Dict[str, bool] = entry["matched_fields"]

            actions = db.scalars(
                select(OperationalActionHistory)
                .where(OperationalActionHistory.incident_id == cand_id)
                .order_by(asc(OperationalActionHistory.timestamp))
            ).all()

            outcome_score, outcome_summary = HybridScorer.compute_outcome_score(actions)
            trust_score = 1.0 # Base trust score
            stale_penalty = StalenessCalculator.calculate_penalty(inc_obj.start_time)

            hybrid_score = HybridScorer.calculate_hybrid_score(
                structured_score=struct_score,
                semantic_score=sem_score,
                outcome_score=outcome_score,
                trust_score=trust_score,
                staleness_penalty=stale_penalty
            )

            if hybrid_score < min_score:
                continue

            failed_actions = [
                {
                    "command": a.command,
                    "tool": a.tool,
                    "target": a.target,
                    "reason": a.reason,
                    "error_message": a.error_message,
                    "idempotency_key": a.idempotency_key,
                } for a in actions if a.result == "FAILED"
            ]

            successful_actions = [
                {
                    "command": a.command,
                    "tool": a.tool,
                    "target": a.target,
                    "reason": a.reason,
                    "idempotency_key": a.idempotency_key,
                } for a in actions if a.result == "SUCCESS"
            ]

            snap = db.scalars(
                select(InfrastructureSnapshot).where(InfrastructureSnapshot.incident_id == cand_id)
            ).first()
            snap_summary = {
                "db_version": snap.db_version if snap else "N/A",
                "service_version": snap.service_version if snap else "N/A",
                "region": snap.region if snap else inc_obj.region,
            }

            memories = db.scalars(
                select(InstitutionalMemoryVector).where(InstitutionalMemoryVector.incident_id == cand_id)
            ).all()
            memory_list = [
                {
                    "id": m.id,
                    "title": m.title,
                    "memory_type": m.memory_type,
                    "content": m.content,
                } for m in memories
            ]

            evidence_items = db.scalars(
                select(IncidentEvidence).where(IncidentEvidence.incident_id == cand_id)
            ).all()

            scored_candidates.append({
                "incident_id": inc_obj.id,
                "title": inc_obj.title,
                "service": inc_obj.service,
                "region": inc_obj.region,
                "severity": inc_obj.severity.value if hasattr(inc_obj.severity, "value") else str(inc_obj.severity),
                "status": inc_obj.status.value if hasattr(inc_obj.status, "value") else str(inc_obj.status),
                "start_time": inc_obj.start_time.isoformat(),
                "hybrid_score": hybrid_score,
                "structured_score": struct_score,
                "semantic_score": sem_score,
                "outcome_score": outcome_score,
                "trust_score": trust_score,
                "staleness_penalty": stale_penalty,
                "matched_fields": matched_fields,
                "outcome_summary": outcome_summary,
                "failed_actions": failed_actions if include_failed_actions else [],
                "successful_actions": successful_actions,
                "infrastructure_snapshot_summary": snap_summary,
                "memory_records": memory_list,
                "evidence_ids": [e.id for e in evidence_items],
            })

        # Sort descending by hybrid score
        scored_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        top_candidates = scored_candidates[:limit]

        # Format output with 1-indexed ranks
        response_candidates: List[HistoricalMemoryCandidateResponse] = []
        for rank, cand in enumerate(top_candidates, start=1):
            cand["rank"] = rank
            response_candidates.append(HistoricalMemoryCandidateResponse(**cand))

        return SimilarIncidentsResponse(
            target_incident_id=incident_id,
            candidates_count=len(response_candidates),
            candidates=response_candidates
        )
