"""Stage 2 Operational Memory & Incident Ingestion Schema

Revision ID: 002_stage2_operational_memory
Revises: 001_initial_schema
Create Date: 2026-08-17 23:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_stage2_operational_memory'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add new columns to incidents
    op.add_column('incidents', sa.Column('service', sa.String(length=100), server_default='web-service', nullable=False))
    op.add_column('incidents', sa.Column('region', sa.String(length=50), server_default='us-east-1', nullable=False))
    op.add_column('incidents', sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('incidents', sa.Column('end_time', sa.DateTime(timezone=True), nullable=True))
    op.add_column('incidents', sa.Column('environment_fingerprint', sa.JSON(), server_default='{}', nullable=False))
    op.add_column('incidents', sa.Column('memory_status', sa.String(length=50), server_default='COMPLETED', nullable=False))
    
    op.create_index(op.f('ix_incidents_service'), 'incidents', ['service'], unique=False)
    op.create_index(op.f('ix_incidents_region'), 'incidents', ['region'], unique=False)

    # 2. Add new columns to institutional_memory_vectors
    op.add_column('institutional_memory_vectors', sa.Column('redacted_content', sa.Text(), nullable=True))
    op.add_column('institutional_memory_vectors', sa.Column('memory_type', sa.String(length=50), server_default='symptom', nullable=False))
    op.add_column('institutional_memory_vectors', sa.Column('evidence_references', sa.JSON(), server_default='[]', nullable=False))
    op.create_index(op.f('ix_institutional_memory_vectors_memory_type'), 'institutional_memory_vectors', ['memory_type'], unique=False)
    op.create_index(op.f('ix_institutional_memory_vectors_incident_id'), 'institutional_memory_vectors', ['incident_id'], unique=False)

    # 3. Create incident_evidence table
    op.create_table(
        'incident_evidence',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('incident_id', sa.String(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('source_event_id', sa.String(length=255), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('trust_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'VERIFIED_GOLD', name='trustlevel'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'source_event_id', name='uq_evidence_source_event_id')
    )
    op.create_index(op.f('ix_incident_evidence_content_hash'), 'incident_evidence', ['content_hash'], unique=False)

    # 4. Create infrastructure_snapshots table
    op.create_table(
        'infrastructure_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('incident_id', sa.String(), nullable=False),
        sa.Column('snapshot_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('db_version', sa.String(length=100), nullable=False),
        sa.Column('service_version', sa.String(length=100), nullable=False),
        sa.Column('topology', sa.JSON(), nullable=False),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('dependencies', sa.JSON(), nullable=False),
        sa.Column('resource_identifiers', sa.JSON(), nullable=False),
        sa.Column('region', sa.String(length=50), nullable=False),
        sa.Column('traffic_info', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Create operational_actions table
    op.create_table(
        'operational_actions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('incident_id', sa.String(), nullable=False),
        sa.Column('saga_id', sa.String(length=255), nullable=True),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('agent', sa.String(length=100), nullable=False),
        sa.Column('command', sa.String(length=255), nullable=False),
        sa.Column('tool', sa.String(length=100), nullable=False),
        sa.Column('target', sa.String(length=512), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('authorization', sa.String(length=100), quote=True, nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('result', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uq_action_idempotency_key')
    )
    op.create_index(op.f('ix_operational_actions_idempotency_key'), 'operational_actions', ['idempotency_key'], unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_operational_actions_idempotency_key'), table_name='operational_actions')
    op.drop_table('operational_actions')
    op.drop_table('infrastructure_snapshots')
    op.drop_index(op.f('ix_incident_evidence_content_hash'), table_name='incident_evidence')
    op.drop_table('incident_evidence')
    op.drop_index(op.f('ix_institutional_memory_vectors_incident_id'), table_name='institutional_memory_vectors')
    op.drop_index(op.f('ix_institutional_memory_vectors_memory_type'), table_name='institutional_memory_vectors')
    op.drop_column('institutional_memory_vectors', 'evidence_references')
    op.drop_column('institutional_memory_vectors', 'memory_type')
    op.drop_column('institutional_memory_vectors', 'redacted_content')
    op.drop_index(op.f('ix_incidents_region'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_service'), table_name='incidents')
    op.drop_column('incidents', 'memory_status')
    op.drop_column('incidents', 'environment_fingerprint')
    op.drop_column('incidents', 'end_time')
    op.drop_column('incidents', 'start_time')
    op.drop_column('incidents', 'region')
    op.drop_column('incidents', 'service')
