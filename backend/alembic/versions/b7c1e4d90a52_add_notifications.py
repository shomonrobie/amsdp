"""add notifications outbox

Sequence 3 (M9-D/E). Forward-only and idempotent: every object is created with
an existence guard so re-running against a partially-migrated database is safe.

Revision ID: b7c1e4d90a52
Revises: a1f2b3c4d5e6
Create Date: 2026-11-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c1e4d90a52'
down_revision: Union[str, Sequence[str], None] = 'a1f2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return bind.dialect.has_table(bind, name)


def _has_index(name: str) -> bool:
    bind = op.get_bind()
    row = bind.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :n"), {"n": name}
    ).fetchone()
    return row is not None


def upgrade() -> None:
    """Create the notification outbox table (idempotent)."""
    if _has_table('notifications'):
        return
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('branch_id', sa.String(), nullable=True),
        sa.Column('appointment_id', sa.String(), nullable=True),
        sa.Column('queue_entry_id', sa.String(), nullable=True),
        sa.Column('patient_id', sa.String(), nullable=True),
        sa.Column('notification_type', sa.String(length=40), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('recipient_mobile', sa.String(length=30), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('dedup_key', sa.String(length=160), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provider', sa.String(length=40), nullable=True),
        sa.Column('provider_message_id', sa.String(length=120), nullable=True),
        sa.Column('error', sa.String(length=500), nullable=True),
        sa.Column('cancel_reason', sa.String(length=200), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dedup_key', name='uq_notification_dedup_key'),
    )
    for name, cols in (("idx_notif_org_status", ['organization_id', 'status']),
                       ("idx_notif_due", ['status', 'scheduled_at']),
                       ("idx_notif_appointment", ['appointment_id'])):
        if not _has_index(name):
            op.create_index(name, 'notifications', cols, unique=False)


def downgrade() -> None:
    """Drop the notification outbox table.

    Destructive by nature; the project's migration policy is forward-only, so
    this exists only to keep the chain reversible in a throwaway database.
    """
    if _has_table('notifications'):
        op.drop_table('notifications')
