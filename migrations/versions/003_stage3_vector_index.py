"""Stage 3 Historical Memory Vector Indexes

Revision ID: 003_stage3_vector_index
Revises: 002_stage2_operational_memory
Create Date: 2026-08-17 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_stage3_vector_index'
down_revision: Union[str, None] = '002_stage2_operational_memory'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Composite indexes for memory retrieval
    op.create_index(
        'ix_memory_incident_type',
        'institutional_memory_vectors',
        ['incident_id', 'memory_type'],
        unique=False
    )

def downgrade() -> None:
    op.drop_index('ix_memory_incident_type', table_name='institutional_memory_vectors')
