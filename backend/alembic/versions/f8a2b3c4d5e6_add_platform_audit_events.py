"""add_platform_audit_events

Revision ID: f8a2b3c4d5e6
Revises: f8a1b2c3d4e5
Create Date: 2026-11-17

O-SaaS-2: Platform-only events belong in ``platform_audit_events``; tenant-
affecting events belong in ``audit_events`` with a non-null ``organization_id``.
This migration adds the platform_audit_events table, which has NO
organization_id — platform events are not scoped to a tenant.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f8a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'f8a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not inspector.has_table('platform_audit_events'):
        op.create_table(
            'platform_audit_events',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('service', sa.String(length=50), nullable=False),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('target_type', sa.String(length=50), nullable=False),
            sa.Column('target_id', sa.String(), nullable=False),
            sa.Column('actor_id', sa.String(), nullable=False),
            sa.Column('actor_role', sa.String(length=30), nullable=False),
            sa.Column('before', sa.JSON(), nullable=True),
            sa.Column('after', sa.JSON(), nullable=True),
            sa.Column('reason', sa.Text(), nullable=False, server_default=''),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(
            'idx_platform_audit_action',
            'platform_audit_events', ['action'],
        )
        op.create_index(
            'idx_platform_audit_time',
            'platform_audit_events', ['timestamp'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if inspector.has_table('platform_audit_events'):
        op.drop_index('idx_platform_audit_time',
                      table_name='platform_audit_events')
        op.drop_index('idx_platform_audit_action',
                      table_name='platform_audit_events')
        op.drop_table('platform_audit_events')