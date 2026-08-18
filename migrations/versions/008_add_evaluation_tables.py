"""add evaluation runs and case results tables

Revision ID: 008_add_evaluation_tables
Revises: 007_add_cdc_tables
Create Date: 2026-08-18 20:49:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008_add_evaluation_tables'
down_revision: Union[str, None] = '007_add_cdc_tables'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None

def upgrade() -> None:
    # Create evaluation_runs table
    op.create_table(
        'evaluation_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dataset_version', sa.String(length=100), nullable=False, server_default='ghostops-golden-v1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'),
        sa.Column('total_cases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('precision_at_1', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('precision_at_3', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mrr', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('temporal_verdict_accuracy', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('evidence_grounding_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('unsafe_replay_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('false_execution_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('regression_gate_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('gate_details', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('duration_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evaluation_runs_dataset_version', 'evaluation_runs', ['dataset_version'])
    op.create_index('ix_evaluation_runs_status', 'evaluation_runs', ['status'])

    # Create evaluation_case_results table
    op.create_table(
        'evaluation_case_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('evaluation_run_id', sa.String(length=36), nullable=False),
        sa.Column('benchmark_id', sa.String(length=100), nullable=False),
        sa.Column('incident_id', sa.String(length=255), nullable=False),
        sa.Column('case_category', sa.String(length=100), nullable=False),
        sa.Column('expected_root_cause', sa.String(length=255), nullable=False),
        sa.Column('actual_hypothesis', sa.String(length=255), nullable=False),
        sa.Column('expected_precedent_id', sa.String(length=255), nullable=True),
        sa.Column('retrieved_precedent_id', sa.String(length=255), nullable=True),
        sa.Column('retrieval_rank', sa.Integer(), nullable=True),
        sa.Column('retrieval_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expected_temporal_verdict', sa.String(length=100), nullable=False),
        sa.Column('actual_temporal_verdict', sa.String(length=100), nullable=False),
        sa.Column('expected_safety_outcome', sa.String(length=100), nullable=False),
        sa.Column('actual_safety_outcome', sa.String(length=100), nullable=False),
        sa.Column('decision_match', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('safety_match', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('would_execute', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('unsafe_execution', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('evidence_grounding_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('trace_details', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['evaluation_run_id'], ['evaluation_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evaluation_case_results_run_id', 'evaluation_case_results', ['evaluation_run_id'])
    op.create_index('ix_evaluation_case_results_benchmark_id', 'evaluation_case_results', ['benchmark_id'])
    op.create_index('ix_evaluation_case_results_incident_id', 'evaluation_case_results', ['incident_id'])
    op.create_index('ix_evaluation_case_results_case_category', 'evaluation_case_results', ['case_category'])

def downgrade() -> None:
    op.drop_table('evaluation_case_results')
    op.drop_table('evaluation_runs')
