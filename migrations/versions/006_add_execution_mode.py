"""add execution_mode column to remediation tables

Revision ID: 006_add_execution_mode
Revises: 005_sync_schemas
Create Date: 2026-08-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006_add_execution_mode'
down_revision: Union[str, None] = '005_sync_schemas'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add execution_mode column to remediation_executions, execution_step_records, and operational_actions
    bind = op.get_bind()
    insp = sa.inspect(bind)

    def add_col_if_missing(table_name, col_name, col_type, default_val):
        existing_cols = [c['name'] for c in insp.get_columns(table_name)]
        if col_name not in existing_cols:
            op.add_column(
                table_name,
                sa.Column(col_name, col_type, nullable=False, server_default=default_val)
            )

    add_col_if_missing('remediation_executions', 'execution_mode', sa.String(50), 'MOCK')
    add_col_if_missing('execution_step_records', 'execution_mode', sa.String(50), 'MOCK')
    add_col_if_missing('operational_actions', 'execution_mode', sa.String(50), 'MOCK')

def downgrade() -> None:
    op.drop_column('operational_actions', 'execution_mode')
    op.drop_column('execution_step_records', 'execution_mode')
    op.drop_column('remediation_executions', 'execution_mode')
