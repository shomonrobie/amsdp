"""drop_redundant_tracking_token_index

Revision ID: e6c1a9b3d5f8
Revises: d4b2c8e1f7a3
Create Date: 2026-11-10

Sequence 4 finding SEQ4-INDEX-P3.

``a1f2b3c4d5e6`` created ``tracking_tokens`` with both

    UniqueConstraint('token_hash')            -- backs tracking_tokens_token_hash_key
    CREATE INDEX ix_tracking_tokens_hash ...  -- same single column, not unique

A UNIQUE constraint in PostgreSQL is implemented as a unique B-tree index on the
same column, so ``ix_tracking_tokens_hash`` is fully redundant: every lookup it
could serve (equality on ``token_hash``) is served by the unique index, and it
only adds a second write per INSERT/UPDATE/DELETE plus a duplicate planner
candidate.  Dropping it changes no query plan for the only access path
(hash equality lookup).

Forward-only and idempotent: ``DROP INDEX IF EXISTS`` makes a re-run a no-op, and
the ``downgrade`` recreates the index only when it is absent, so the revision can
be rolled back without duplicating the object.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e6c1a9b3d5f8'
down_revision: Union[str, Sequence[str], None] = 'd4b2c8e1f7a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    if not sa.inspect(connection).has_table('tracking_tokens'):
        return
    # Keep the constraint-backed unique index; drop only the duplicate.
    op.execute("DROP INDEX IF EXISTS ix_tracking_tokens_hash")


def downgrade() -> None:
    connection = op.get_bind()
    if not sa.inspect(connection).has_table('tracking_tokens'):
        return
    op.execute("CREATE INDEX IF NOT EXISTS ix_tracking_tokens_hash "
               "ON tracking_tokens (token_hash)")
