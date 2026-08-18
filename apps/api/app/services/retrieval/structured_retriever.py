from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import Incident, InfrastructureSnapshot, IncidentEvidence
from app.services.retrieval.fingerprint import IncidentFingerprint
from app.core.config import settings

class StructuredMemoryRetriever:
    """
    Retrieves candidate historical incidents from CockroachDB matching structured metadata signals.
    Exposes explicit matched_fields for full explainability.
    """

    @staticmethod
    def retrieve_candidates(
        db: Session,
        fingerprint: IncidentFingerprint,
        exclude_incident_id: Optional[str] = None
    ) -> List[Tuple[Incident, float, Dict[str, bool]]]:
        stmt = select(Incident)
        if exclude_incident_id:
            stmt = stmt.where(Incident.id != exclude_incident_id)

        stmt = stmt.limit(settings.RETRIEVAL_STRUCTURED_POOL_SIZE)
        incidents = db.scalars(stmt).all()

        candidates: List[Tuple[Incident, float, Dict[str, bool]]] = []

        for inc in incidents:
            snapshot = db.scalars(
                select(InfrastructureSnapshot).where(InfrastructureSnapshot.incident_id == inc.id)
            ).first()
            evidence = db.scalars(
                select(IncidentEvidence).where(IncidentEvidence.incident_id == inc.id)
            ).all()

            cand_fp = IncidentFingerprint.from_incident(inc, snapshot, evidence)

            # Evaluate structured field matches
            service_match = (cand_fp.service == fingerprint.service)
            region_match = (cand_fp.region == fingerprint.region)
            symptom_match = bool(set(cand_fp.symptoms) & set(fingerprint.symptoms))
            resource_type_match = bool(set(cand_fp.resource_types) & set(fingerprint.resource_types))
            db_version_match = (cand_fp.db_version == fingerprint.db_version)
            service_version_match = (cand_fp.service_version == fingerprint.service_version)

            matched_fields = {
                "service": service_match,
                "region": region_match,
                "symptom": symptom_match,
                "resource_type": resource_type_match,
                "db_version": db_version_match,
                "service_version": service_version_match,
            }

            # Structured match score: Symptom match is load-bearing
            raw_score = (
                (0.40 if symptom_match else 0.0) +
                (0.30 if service_match else 0.0) +
                (0.10 if db_version_match else 0.0) +
                (0.10 if service_version_match else 0.0) +
                (0.05 if region_match else 0.0) +
                (0.05 if resource_type_match else 0.0)
            )

            # Symptom mismatch penalty (0.2 multiplier): Completely different symptom types must rank lower
            final_score = raw_score if symptom_match else raw_score * 0.2

            candidates.append((inc, round(final_score, 4), matched_fields))

        return candidates
