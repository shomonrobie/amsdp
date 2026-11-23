"""add_queue_announcement_deliveries

Revision ID: a7c3f19d2b64
Revises: a9c4e1f7b2d8
Create Date: 2026-11-21

QUE-006 / W2: cross-terminal announcement delivery claim (POD-4 + POD-8 / V-12).

TRIAL MERGE CORRECTION (QUE-006 integration trial, 2026-11-22) — PROPOSED, NOT ACCEPTED:
this migration declared ``Revises: f8a2b3c4d5e6``, a revision that is already an
*ancestor* of the current head ``a9c4e1f7b2d8`` (``a9c4e1f7b2d8`` is a merge revision
whose tuple parent list includes ``f8a2b3c4d5e6``). Branching there left the graph
with **two heads** (``a9c4e1f7b2d8`` and ``c4d8e2a91f60``), so
``alembic upgrade head`` refused with "Multiple head revisions are present" — verified
at runtime against a restored backup in a disposable PostgreSQL 17 container.
Reparenting to ``a9c4e1f7b2d8`` (the head the live Ubuntu database is already on)
restores a single linear chain and one head, ``c4d8e2a91f60``. Nothing else in this
file changes; the DDL is unchanged and remains forward-only and idempotent.

One row per queue call event. ``call_event_id`` is derived on the server from
``queue_entries.status_history`` (``backend/queuing/events.py``) and is UNIQUE,
so the first terminal to insert the claim wins and every later terminal is
refused — that is the whole cross-terminal duplicate protection. The row also
carries the announcement outcome (``requested`` -> ``completed`` / ``failed`` /
``blocked`` / ``interrupted`` / ``skipped_busy``), which is what distinguishes a
successful *queue call* from a completed *audio playback*.

Forward-only and idempotent: the table and its indexes are created only when
absent, so re-running against a database that already has them is a no-op.
No existing table, column, constraint or row is modified.

Retention: rows are never deleted by this migration or by the application; the
announcement audit trail follows the same retention policy as ``audit_events``.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a7c3f19d2b64'
down_revision: Union[str, Sequence[str], None] = 'a9c4e1f7b2d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = 'queue_announcement_deliveries'


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not inspector.has_table(TABLE):
        op.create_table(
            TABLE,
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('branch_id', sa.String(), nullable=True),
            sa.Column('queue_entry_id', sa.String(), nullable=False),
            sa.Column('call_event_id', sa.String(length=120), nullable=False),
            sa.Column('language', sa.String(length=8), nullable=False,
                      server_default=''),
            sa.Column('voice_pack_id', sa.String(length=80), nullable=False,
                      server_default=''),
            sa.Column('voice_pack_version', sa.Integer(), nullable=False,
                      server_default='0'),
            sa.Column('transport', sa.String(length=20), nullable=False,
                      server_default=''),
            sa.Column('requested_by', sa.String(), nullable=False),
            sa.Column('requested_by_role', sa.String(length=30), nullable=True),
            sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', sa.String(length=24), nullable=False,
                      server_default='requested'),
            sa.Column('outcome_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('outcome_reason', sa.String(length=120), nullable=False,
                      server_default=''),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
            sa.ForeignKeyConstraint(['queue_entry_id'], ['queue_entries.id']),
            sa.UniqueConstraint('call_event_id',
                                name='queue_announcement_deliveries_call_event_id_key'),
        )

    existing = {ix['name'] for ix in inspector.get_indexes(TABLE)}
    if 'idx_queue_announcement_entry' not in existing:
        op.create_index('idx_queue_announcement_entry', TABLE, ['queue_entry_id'])
    if 'idx_queue_announcement_org_time' not in existing:
        op.create_index('idx_queue_announcement_org_time', TABLE,
                        ['organization_id', 'requested_at'])


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if inspector.has_table(TABLE):
        existing = {ix['name'] for ix in inspector.get_indexes(TABLE)}
        if 'idx_queue_announcement_org_time' in existing:
            op.drop_index('idx_queue_announcement_org_time', table_name=TABLE)
        if 'idx_queue_announcement_entry' in existing:
            op.drop_index('idx_queue_announcement_entry', table_name=TABLE)
        op.drop_table(TABLE)
