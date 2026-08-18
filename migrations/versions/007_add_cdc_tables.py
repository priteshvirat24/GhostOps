"""add cdc processed events and stream cursor tables

Revision ID: 007_add_cdc_tables
Revises: 006_add_execution_mode
Create Date: 2026-08-18 20:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007_add_cdc_tables'
down_revision: Union[str, None] = '006_add_execution_mode'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None

def upgrade() -> None:
    # Create cdc_processed_events table
    op.create_table(
        'cdc_processed_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('source_table', sa.String(length=100), nullable=False),
        sa.Column('primary_key', sa.String(length=255), nullable=False),
        sa.Column('operation', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PROCESSED'),
        sa.Column('propagated_trust_delta', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('payload_snapshot', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('processing_metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cdc_processed_events_event_id', 'cdc_processed_events', ['event_id'], unique=True)
    op.create_index('ix_cdc_processed_events_source_table', 'cdc_processed_events', ['source_table'])
    op.create_index('ix_cdc_processed_events_primary_key', 'cdc_processed_events', ['primary_key'])

    # Create cdc_stream_cursors table
    op.create_table(
        'cdc_stream_cursors',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('feed_name', sa.String(length=100), nullable=False),
        sa.Column('last_resolved_timestamp', sa.String(length=255), nullable=False),
        sa.Column('events_processed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_event_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cdc_stream_cursors_feed_name', 'cdc_stream_cursors', ['feed_name'], unique=True)

def downgrade() -> None:
    op.drop_table('cdc_stream_cursors')
    op.drop_table('cdc_processed_events')
