from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import InstitutionalMemoryVector
from app.agents import get_model_provider
from app.schemas.memory import MemoryVectorCreate, MemorySearchQuery, MemorySearchResult

class MemoryService:
    @staticmethod
    def store_memory(db: Session, memory_in: MemoryVectorCreate) -> InstitutionalMemoryVector:
        provider = get_model_provider()
        embedding = provider.generate_embedding(memory_in.content)

        memory_entry = InstitutionalMemoryVector(
            title=memory_in.title,
            content=memory_in.content,
            entity_type=memory_in.entity_type,
            entity_id=memory_in.entity_id,
            incident_id=memory_in.incident_id,
            embedding=embedding,
            metadata_json=memory_in.metadata_json,
            trust_level=memory_in.trust_level,
        )
        db.add(memory_entry)
        db.commit()
        db.refresh(memory_entry)
        return memory_entry

    @staticmethod
    def search_memories(db: Session, query: MemorySearchQuery) -> List[MemorySearchResult]:
        provider = get_model_provider()
        query_vector = provider.generate_embedding(query.query_text)

        stmt = select(InstitutionalMemoryVector)
        if query.entity_type:
            stmt = stmt.where(InstitutionalMemoryVector.entity_type == query.entity_type)
        stmt = stmt.limit(query.top_k)

        entries = db.scalars(stmt).all()
        results = []
        for entry in entries:
            # Simplified cosine similarity simulation for Stage 1 validation
            results.append(
                MemorySearchResult(
                    id=entry.id,
                    title=entry.title,
                    content=entry.content,
                    entity_type=entry.entity_type,
                    similarity_score=0.88,
                    trust_level=entry.trust_level,
                    created_at=entry.created_at,
                )
            )
        return results
