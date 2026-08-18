from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Incident, IncidentEvent
from app.schemas.incident import IncidentCreate

class IncidentService:
    @staticmethod
    def get_incidents(db: Session, limit: int = 50) -> List[Incident]:
        stmt = select(Incident).order_by(Incident.created_at.desc()).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_incident_by_id(db: Session, incident_id: str) -> Optional[Incident]:
        return db.get(Incident, incident_id)

    @staticmethod
    def create_incident(db: Session, incident_in: IncidentCreate) -> Incident:
        incident = Incident(
            title=incident_in.title,
            description=incident_in.description,
            severity=incident_in.severity,
            target_resource_id=incident_in.target_resource_id,
        )
        db.add(incident)
        db.flush()

        for event_in in incident_in.events:
            event = IncidentEvent(
                incident_id=incident.id,
                event_source=event_in.event_source,
                event_name=event_in.event_name,
                event_timestamp=event_in.event_timestamp,
                payload=event_in.payload,
            )
            db.add(event)

        db.commit()
        db.refresh(incident)
        return incident
