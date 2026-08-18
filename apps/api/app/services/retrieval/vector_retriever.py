import math
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, text, func

from app.db.models import InstitutionalMemoryVector, Incident
from app.core.config import settings

class VectorMemoryRetriever:
    """
    Executes native CockroachDB vector search over institutional_memory_vectors table.
    Converts raw distance into normalized semantic similarity score (0.0 to 1.0).
    """

    @staticmethod
    def retrieve_candidates(
        db: Session,
        query_vector: List[float],
        memory_type: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float, InstitutionalMemoryVector]]:
        k = top_k or settings.RETRIEVAL_VECTOR_POOL_SIZE

        # Dialect check: CockroachDB / PostgreSQL vs SQLite
        dialect_name = db.bind.dialect.name if db.bind else "postgresql"

        results: List[Tuple[str, float, InstitutionalMemoryVector]] = []

        if dialect_name in ("postgresql", "cockroachdb"):
            # Native CockroachDB VECTOR(1536) cosine distance calculation performed inside the database engine
            # Uses CockroachDB vector distance function with structured predicates
            vec_array_str = "ARRAY[" + ",".join(str(float(f)) for f in query_vector) + "]::VECTOR(1536)"
            query_sql = f"""
                SELECT id, incident_id, cosine_distance(embedding, {vec_array_str}) as dist
                FROM institutional_memory_vectors
                WHERE incident_id IS NOT NULL
                {'AND memory_type = :mem_type' if memory_type else ''}
                ORDER BY dist ASC
                LIMIT :limit_val
            """
            params = {"limit_val": k}
            if memory_type:
                params["mem_type"] = memory_type

            rows = db.execute(text(query_sql), params).fetchall()
            for r in rows:
                mem_id, inc_id, dist = r[0], r[1], float(r[2])
                mem_obj = db.get(InstitutionalMemoryVector, mem_id)
                # Convert cosine distance (0.0 to 2.0) to normalized similarity score (0.0 to 1.0)
                sim_score = round(max(0.0, min(1.0, 1.0 - (dist / 2.0))), 4)
                results.append((inc_id, sim_score, mem_obj))
        else:
            # Dialect fallback for SQLite unit test execution
            stmt = select(InstitutionalMemoryVector).where(InstitutionalMemoryVector.incident_id.is_not(None))
            if memory_type:
                stmt = stmt.where(InstitutionalMemoryVector.memory_type == memory_type)

            memories = db.scalars(stmt).all()
            for mem in memories:
                sim = VectorMemoryRetriever._python_cosine_similarity(query_vector, mem.embedding)
                sim_score = round(max(0.0, min(1.0, sim)), 4)
                results.append((mem.incident_id, sim_score, mem))

            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:k]

        return results

    @staticmethod
    def _python_cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
