"""Stage 4 CockroachDB Native VECTOR(1536) Storage and Indexing

Revision ID: 004_cockroach_native_vector
Revises: 003_stage3_vector_index
Create Date: 2026-08-18 15:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_cockroach_native_vector'
down_revision: Union[str, None] = '003_stage3_vector_index'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect in ("postgresql", "cockroachdb"):
        # 1. Add summary_embedding to incidents table as native CockroachDB VECTOR(1536)
        op.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS summary_embedding VECTOR(1536)")

        # 2. Alter institutional_memory_vectors.embedding to native VECTOR(1536)
        op.execute(
            "ALTER TABLE institutional_memory_vectors ALTER COLUMN embedding TYPE VECTOR(1536) "
            "USING embedding::VECTOR(1536)"
        )



        # 4. Create CockroachDB vector index on institutional_memory_vectors
        op.execute(
            "CREATE VECTOR INDEX IF NOT EXISTS ix_memory_vectors_embedding "
            "ON institutional_memory_vectors (embedding)"
        )
    else:
        # SQLite dialect fallback for local/unit test environment
        # Use inspector to safely add column only if not already present
        inspector = sa.inspect(bind)
        cols = [c['name'] for c in inspector.get_columns('incidents')]
        if 'summary_embedding' not in cols:
            op.add_column('incidents', sa.Column('summary_embedding', sa.JSON(), nullable=True))

def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect in ("postgresql", "cockroachdb"):
        op.execute("DROP INDEX IF EXISTS ix_memory_vectors_embedding")
        op.execute(
            "ALTER TABLE institutional_memory_vectors ALTER COLUMN embedding TYPE FLOAT8[] "
            "USING embedding::FLOAT8[]"
        )

        op.execute("ALTER TABLE incidents DROP COLUMN IF EXISTS summary_embedding")
    else:
        inspector = sa.inspect(bind)
        cols = [c['name'] for c in inspector.get_columns('incidents')]
        if 'summary_embedding' in cols:
            op.drop_column('incidents', 'summary_embedding')
