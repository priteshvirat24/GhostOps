from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.memory_service import MemoryService
from app.services.retrieval.vector_retriever import VectorMemoryRetriever
from app.schemas.memory import MemoryVectorCreate, MemorySearchQuery, MemorySearchResult
from app.schemas.retrieval import MemorySearchRequestPayload
from app.agents import get_model_provider

router = APIRouter()

@router.post("/store", response_model=dict)
def store_memory(memory_in: MemoryVectorCreate, db: Session = Depends(get_db)):
    entry = MemoryService.store_memory(db, memory_in)
    return {"id": entry.id, "title": entry.title, "status": "stored"}

@router.post("/search", response_model=List[Dict[str, Any]])
def search_memory(payload: MemorySearchRequestPayload, db: Session = Depends(get_db)):
    """POST /api/v1/memory/search - General memory vector search endpoint for query text."""
    provider = get_model_provider()
    query_vector = provider.generate_embedding(payload.query_text)

    vector_candidates = VectorMemoryRetriever.retrieve_candidates(
        db=db,
        query_vector=query_vector,
        memory_type=payload.memory_type,
        top_k=payload.limit
    )

    results = []
    for inc_id, sim_score, mem_obj in vector_candidates:
        results.append({
            "memory_id": mem_obj.id,
            "incident_id": inc_id,
            "title": mem_obj.title,
            "memory_type": mem_obj.memory_type,
            "content": mem_obj.content,
            "similarity_score": sim_score,
            "trust_level": mem_obj.trust_level.value if hasattr(mem_obj.trust_level, "value") else str(mem_obj.trust_level),
            "created_at": mem_obj.created_at.isoformat() if mem_obj.created_at else None,
        })
    return results
