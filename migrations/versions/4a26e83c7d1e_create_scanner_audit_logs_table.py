"""create scanner audit logs table

Revision ID: 4a26e83c7d1e
Revises: 298ee32a6d4d
Create Date: 2026-08-29 14:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a26e83c7d1e'
down_revision: Union[str, Sequence[str], None] = '298ee32a6d4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scanner_audit_logs',
        sa.Column('log_id', sa.String(length=50), nullable=False),
        sa.Column('scanner_type', sa.String(length=20), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=True),
        sa.Column('similarity', sa.Float(), nullable=True),
        sa.Column('message', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id']),
        sa.PrimaryKeyConstraint('log_id'),
    )
    op.create_index(
        'ix_scanner_audit_logs_created_at',
        'scanner_audit_logs',
        ['created_at'],
        unique=False,
    )
    op.create_index(
        'ix_scanner_audit_logs_employee_id',
        'scanner_audit_logs',
        ['employee_id'],
        unique=False,
    )
    op.create_index(
        'ix_scanner_audit_logs_event_type',
        'scanner_audit_logs',
        ['event_type'],
        unique=False,
    )
    op.create_index(
        'ix_scanner_audit_logs_status',
        'scanner_audit_logs',
        ['status'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_scanner_audit_logs_status', table_name='scanner_audit_logs')
    op.drop_index('ix_scanner_audit_logs_event_type', table_name='scanner_audit_logs')
    op.drop_index('ix_scanner_audit_logs_employee_id', table_name='scanner_audit_logs')
    op.drop_index('ix_scanner_audit_logs_created_at', table_name='scanner_audit_logs')
    op.drop_table('scanner_audit_logs')
