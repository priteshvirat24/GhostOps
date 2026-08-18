from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.db.models import Incident, InfrastructureSnapshot, IncidentEvidence

class IncidentFingerprint(BaseModel):
    service: str = "unknown-service"
    region: str = "us-east-1"
    severity: str = "MEDIUM"
    symptoms: List[str] = Field(default_factory=list)
    resource_types: List[str] = Field(default_factory=list)
    resource_ids: List[str] = Field(default_factory=list)
    service_version: str = "v1.0.0"
    db_version: str = "CockroachDB v23.2.3"
    topology_summary: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_incident(
        cls,
        incident: Incident,
        snapshot: Optional[InfrastructureSnapshot] = None,
        evidence: Optional[List[IncidentEvidence]] = None
    ) -> "IncidentFingerprint":
        symptoms: List[str] = []
        resource_types: List[str] = []
        resource_ids: List[str] = []

        if incident.target_resource_id:
            resource_ids.append(incident.target_resource_id)

        # Extract symptoms & event types from evidence
        if evidence:
            for ev in evidence:
                if ev.event_type and ev.event_type not in symptoms:
                    symptoms.append(ev.event_type)
                if ev.source and ev.source not in resource_types:
                    resource_types.append(ev.source)

        if incident.title:
            symptoms.append(incident.title.lower())

        svc_ver = (snapshot.service_version if snapshot and snapshot.service_version else "v1.0.0")
        db_ver = (snapshot.db_version if snapshot and snapshot.db_version else "CockroachDB v23.2.3")
        topo = (snapshot.topology if snapshot and snapshot.topology else {})

        return cls(
            service=incident.service or "web-service",
            region=incident.region or "us-east-1",
            severity=incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity),
            symptoms=symptoms,
            resource_types=resource_types,
            resource_ids=resource_ids,
            service_version=svc_ver,
            db_version=db_ver,
            topology_summary=topo
        )

    def to_canonical_text(self) -> str:
        """
        Produces a canonical textual representation for semantic embedding generation.
        """
        symptom_str = ", ".join(self.symptoms) if self.symptoms else "telemetry alert"
        return (
            f"Service {self.service} in region {self.region} with severity {self.severity} "
            f"experienced symptoms: {symptom_str}. Running service version {self.service_version} "
            f"and database version {self.db_version}."
        )
