"""add_schedule_blocks

Revision ID: b2e5c7d91a04
Revises: c4d8e2a91f60
Create Date: 2026-11-24

MP-16 / BR §15 — blocked dates and periods.

One additive table, nothing else:

``schedule_blocks``
    one row per blocked period of one schedule: an inclusive ``start_date`` …
    ``end_date`` range and an optional ``start_time``/``end_time`` window
    (both NULL = the whole day).  A cancellation is a status change, never a
    delete, so the record and the audit trail stay reconcilable.

Why a table and not ``organizations.config``
--------------------------------------------
MP-10 could keep the walk-in policy in the existing JSON configuration block
because a policy is a small scalar set.  A block is *dated business data*: it is
queried per doctor and per day on every availability read and every booking, it
is listed per schedule, it is cancelled individually, and each row carries its
own actor and reason.  None of that fits a config blob, and filtering a JSON
array per request would put the availability read on a code path no index can
help.

The two indexes are the access paths the code actually uses:
``idx_block_doctor`` (every availability read / booking guard) and
``idx_block_schedule`` (the schedule's block list, ordered by date).

Forward-only and idempotent: the table and each index are created only when
absent, so re-running against a database that already has them is a no-op.  No
existing table, column, constraint or row is modified.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2e5c7d91a04'
down_revision: Union[str, Sequence[str], None] = 'c4d8e2a91f60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BLOCKS = 'schedule_blocks'


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not inspector.has_table(BLOCKS):
        op.create_table(
            BLOCKS,
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('branch_id', sa.String(), nullable=False),
            sa.Column('schedule_id', sa.String(), nullable=False),
            sa.Column('doctor_id', sa.String(), nullable=False),
            sa.Column('start_date', sa.Date(), nullable=False),
            sa.Column('end_date', sa.Date(), nullable=False),
            sa.Column('start_time', sa.String(length=5), nullable=True),
            sa.Column('end_time', sa.String(length=5), nullable=True),
            sa.Column('reason', sa.String(length=200), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False,
                      server_default='active'),
            sa.Column('created_by', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('cancelled_by', sa.String(), nullable=True),
            sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('cancel_reason', sa.String(length=200), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
            sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id']),
            sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id']),
            # An inverted range would block nothing while looking authoritative.
            sa.CheckConstraint('end_date >= start_date',
                               name='ck_block_dates_ordered'),
        )

    existing = {ix['name'] for ix in inspector.get_indexes(BLOCKS)}
    if 'idx_block_doctor' not in existing:
        op.create_index('idx_block_doctor', BLOCKS, ['doctor_id', 'start_date'])
    if 'idx_block_schedule' not in existing:
        op.create_index('idx_block_schedule', BLOCKS,
                        ['schedule_id', 'start_date'])
    if 'idx_block_org' not in existing:
        op.create_index('idx_block_org', BLOCKS, ['organization_id'])


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if inspector.has_table(BLOCKS):
        existing = {ix['name'] for ix in inspector.get_indexes(BLOCKS)}
        for name in ('idx_block_org', 'idx_block_schedule', 'idx_block_doctor'):
            if name in existing:
                op.drop_index(name, table_name=BLOCKS)
        op.drop_table(BLOCKS)
