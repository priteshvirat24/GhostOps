"""Initial GhostOps Database Schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-17 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Incidents Table
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='incidentseverity'), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'INVESTIGATING', 'REMEDIATION_PROPOSED', 'REMEDIATION_IN_PROGRESS', 'VERIFYING', 'RESOLVED', 'CLOSED', name='incidentstatus'), nullable=False),
        sa.Column('target_resource_id', sa.String(length=255), nullable=True),
        sa.Column('root_cause_summary', sa.Text(), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Incident Events Table
    op.create_table(
        'incident_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('incident_id', sa.String(), nullable=False),
        sa.Column('event_source', sa.String(length=100), nullable=False),
        sa.Column('event_name', sa.String(length=255), nullable=False),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Infrastructure Nodes Table
    op.create_table(
        'infrastructure_nodes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('resource_type', sa.Enum('EC2_INSTANCE', 'LAMBDA_FUNCTION', 'ECS_SERVICE', 'SECURITY_GROUP', 'COCKROACH_NODE', 'IAM_ROLE', 'VPC_SUBNET', name='entitytype'), nullable=False),
        sa.Column('arn', sa.String(length=512), nullable=True),
        sa.Column('aws_region', sa.String(length=50), nullable=False),
        sa.Column('state_payload', sa.JSON(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_infrastructure_nodes_is_current'), 'infrastructure_nodes', ['is_current'], unique=False)
    op.create_index(op.f('ix_infrastructure_nodes_resource_id'), 'infrastructure_nodes', ['resource_id'], unique=False)

    # Institutional Memory Vectors Table
    op.create_table(
        'institutional_memory_vectors',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.Enum('EC2_INSTANCE', 'LAMBDA_FUNCTION', 'ECS_SERVICE', 'SECURITY_GROUP', 'COCKROACH_NODE', 'IAM_ROLE', 'VPC_SUBNET', name='entitytype'), nullable=True),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('incident_id', sa.String(length=255), nullable=True),
        sa.Column('embedding', sa.ARRAY(sa.Float()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('trust_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'VERIFIED_GOLD', name='trustlevel'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Remediation Plans Table
    op.create_table(
        'remediation_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('incident_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'EXECUTING', 'EXECUTED', 'VERIFIED_SUCCESS', 'VERIFIED_FAILURE', 'ROLLED_BACK', name='remediationsstatus'), nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('estimated_risk', sa.String(length=50), nullable=False),
        sa.Column('requires_human_approval', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_remediation_plans_idempotency_key'), 'remediation_plans', ['idempotency_key'], unique=True)

    # Plan Steps Table
    op.create_table(
        'plan_steps',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('remediation_plan_id', sa.String(), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('target_resource_arn', sa.String(length=512), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('rollback_parameters', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('execution_result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['remediation_plan_id'], ['remediation_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Agent Traces Table
    op.create_table(
        'agent_traces',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('incident_id', sa.String(), nullable=True),
        sa.Column('graph_name', sa.String(length=100), nullable=False),
        sa.Column('thread_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED', name='agentstepstatus'), nullable=False),
        sa.Column('current_node', sa.String(length=100), nullable=False),
        sa.Column('state_snapshot', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_traces_thread_id'), 'agent_traces', ['thread_id'], unique=False)

    # Agent Step Executions Table
    op.create_table(
        'agent_step_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('trace_id', sa.String(), nullable=False),
        sa.Column('node_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED', name='agentstepstatus'), nullable=False),
        sa.Column('input_state', sa.JSON(), nullable=False),
        sa.Column('output_state', sa.JSON(), nullable=True),
        sa.Column('tool_calls', sa.JSON(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trace_id'], ['agent_traces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('agent_step_executions')
    op.drop_index(op.f('ix_agent_traces_thread_id'), table_name='agent_traces')
    op.drop_table('agent_traces')
    op.drop_table('plan_steps')
    op.drop_index(op.f('ix_remediation_plans_idempotency_key'), table_name='remediation_plans')
    op.drop_table('remediation_plans')
    op.drop_table('institutional_memory_vectors')
    op.drop_index(op.f('ix_infrastructure_nodes_resource_id'), table_name='infrastructure_nodes')
    op.drop_index(op.f('ix_infrastructure_nodes_is_current'), table_name='infrastructure_nodes')
    op.drop_table('infrastructure_nodes')
    op.drop_table('incident_events')
    op.drop_table('incidents')
