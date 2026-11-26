"""add_tracking_rate_buckets

Revision ID: e1b7c4a9d236
Revises: d3f5a7b91c24
Create Date: 2026-11-26

MP-25 / GAP-20 — a durable request budget for the public tracking page.

One **additive** table, and nothing else:

``tracking_rate_buckets``
    ``bucket`` (client address, prefixed) is the primary key; the row carries the
    start of the current fixed window and the number of requests already
    allocated in it.  ``common/rate_limit.py`` allocates it with a single
    ``INSERT … ON CONFLICT DO UPDATE`` so several workers share one budget
    instead of each holding a private one in memory.

Deliberately unchanged
----------------------
No existing table, column, constraint, index or row is touched.  ``tracking_tokens``
is not altered: a token's lifecycle is a separate concern from a caller's request
budget, and the two must be able to expire independently.

Forward-only and idempotent: the table and its index are created only when
absent, so a second ``upgrade head`` on the same database is a no-op.

Not applied here to any deployment database.  This revision was authored and
rendered offline (``alembic upgrade head --sql``) because the environment used to
write it has no PostgreSQL; it must be applied by the approved deployment process
(``alembic current`` first, ``_tools/pg_backup.sh`` before any upgrade).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e1b7c4a9d236'
down_revision: Union[str, Sequence[str], None] = 'd3f5a7b91c24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BUCKETS = 'tracking_rate_buckets'
WINDOW_INDEX = 'idx_rate_bucket_window'


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not inspector.has_table(BUCKETS):
        op.create_table(
            BUCKETS,
            sa.Column('bucket', sa.String(length=120), nullable=False),
            sa.Column('window_started_at', sa.DateTime(timezone=True),
                      nullable=False),
            sa.Column('hits', sa.Integer(), nullable=False,
                      server_default='0'),
            sa.PrimaryKeyConstraint('bucket'),
        )

    existing = {ix['name'] for ix in inspector.get_indexes(BUCKETS)}
    if WINDOW_INDEX not in existing:
        # Housekeeping only: an operator pruning an abandoned table by age needs
        # to find old rows without a sequential scan.  It is not on the hot path,
        # which is a primary-key upsert.
        op.create_index(WINDOW_INDEX, BUCKETS, ['window_started_at'])


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if inspector.has_table(BUCKETS):
        existing = {ix['name'] for ix in inspector.get_indexes(BUCKETS)}
        if WINDOW_INDEX in existing:
            op.drop_index(WINDOW_INDEX, table_name=BUCKETS)
        op.drop_table(BUCKETS)
