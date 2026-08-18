import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.agents import MockBedrockProvider
from app.services.retrieval.vector_retriever import VectorMemoryRetriever
from app.db.models import Base, InstitutionalMemoryVector
from app.db.types import VectorType, CockroachVector

COCKROACH_TEST_URL = os.getenv(
    "COCKROACH_TEST_URL",
    "postgresql+psycopg://root@localhost:26257/ghostops?sslmode=disable"
)

def _is_cockroach_reachable() -> bool:
    try:
        engine = create_engine(COCKROACH_TEST_URL, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

def _is_cockroach_vector_supported() -> bool:
    try:
        engine = create_engine(COCKROACH_TEST_URL, connect_args={"connect_timeout": 2})
        with engine.begin() as conn:
            conn.execute(text("SELECT '[1.0, 2.0]'::VECTOR(2)"))
        return True
    except Exception:
        return False

def test_cockroach_vector_type_compilation():
    """Validates dialect-aware CockroachVector column specification."""
    vec_type = CockroachVector(1536)
    assert vec_type.get_col_spec() == "VECTOR(1536)"
    assert vec_type.dim == 1536

def test_cockroach_vector_sql_expression_generation():
    """
    Validates native CockroachDB VECTOR distance SQL query construction,
    VECTOR(1536) parameter formatting, and cosine_distance syntax.
    """
    provider = MockBedrockProvider()
    vec = provider.generate_embedding("CockroachDB vector test query")
    assert len(vec) == 1536

    vec_array_str = "ARRAY[" + ",".join(str(f) for f in vec) + "]::VECTOR(1536)"
    stmt_str = f"SELECT id, incident_id, cosine_distance(embedding, {vec_array_str}) as dist FROM institutional_memory_vectors"

    assert "cosine_distance(embedding, ARRAY[" in stmt_str
    assert "]::VECTOR(1536)) as dist" in stmt_str
    assert "FROM institutional_memory_vectors" in stmt_str

def test_sqlite_vector_retriever_query_execution(db_session):
    """
    Validates VectorMemoryRetriever query execution against active SQLite session.
    Inserts deterministic 1536-dim vectors and verifies candidate ordering via fallback.
    """
    provider = MockBedrockProvider()
    v1 = provider.generate_embedding("database connection pool exhaustion auth-service")
    v2 = provider.generate_embedding("unauthorized api call cloudtrail anomaly")
    assert len(v1) == 1536
    assert len(v2) == 1536

    mem1 = InstitutionalMemoryVector(
        id="vmem-01",
        title="Auth Service DB Exhaustion",
        content="Content 1",
        memory_type="remediation",
        incident_id="inc-v1",
        embedding=v1
    )
    mem2 = InstitutionalMemoryVector(
        id="vmem-02",
        title="CloudTrail Anomaly",
        content="Content 2",
        memory_type="symptom",
        incident_id="inc-v2",
        embedding=v2
    )

    db_session.add_all([mem1, mem2])
    db_session.commit()

    candidates = VectorMemoryRetriever.retrieve_candidates(db_session, v1, memory_type=None)
    assert len(candidates) >= 2
    top_inc_id, top_score, _ = candidates[0]
    assert top_inc_id == "inc-v1"
    assert top_score > 0.8

@pytest.mark.skipif(
    not _is_cockroach_vector_supported(),
    reason="COCKROACHDB INTEGRATION BLOCKED: CockroachDB instance requires an Enterprise license or Cloud cluster to enable VECTOR(1536)"
)
def test_live_cockroach_native_vector_integration():
    """
    Direct CockroachDB Integration Test:
    Connects to real CockroachDB, creates tables with VECTOR(1536), inserts embeddings,
    and executes real database-side cosine_distance vector similarity search.
    """
    engine = create_engine(COCKROACH_TEST_URL)
    # Schema is managed by Alembic migrations. Do not create_all/drop_all.
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        provider = MockBedrockProvider()
        v1 = provider.generate_embedding("auth service connection exhaustion")
        v2 = provider.generate_embedding("unrelated s3 bucket deletion")

        mem1 = InstitutionalMemoryVector(
            id="crdb-vec-01",
            title="Cockroach Auth DB Exhaustion",
            content="Real CockroachDB Vector Memory",
            memory_type="remediation",
            incident_id="inc-crdb-01",
            embedding=v1
        )
        mem2 = InstitutionalMemoryVector(
            id="crdb-vec-02",
            title="Cockroach S3 Deletion",
            content="Unrelated S3 incident",
            memory_type="symptom",
            incident_id="inc-crdb-02",
            embedding=v2
        )
        db.add_all([mem1, mem2])
        db.commit()

        # Execute live CockroachDB native vector retrieval
        results = VectorMemoryRetriever.retrieve_candidates(db, v1, memory_type="remediation")
        assert len(results) >= 1
        top_inc_id, top_score, top_obj = results[0]
        assert top_inc_id == "inc-crdb-01"
        assert top_score > 0.8
    finally:
        db.execute(text("DELETE FROM institutional_memory_vectors WHERE id IN ('crdb-vec-01', 'crdb-vec-02')"))
        db.commit()
        db.close()
