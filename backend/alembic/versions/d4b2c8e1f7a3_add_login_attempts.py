"""add_login_attempts

Revision ID: d4b2c8e1f7a3
Revises: b7c1e4d90a52
Create Date: 2026-11-10

Durable login throttling (Sequence 4 finding SEQ4-THROTTLE-D1; M8 §10).

Sequence 4 rate-limited ``/api/v1/staff/login`` from a module-level dict, so the
allowance was per process: N uvicorn workers (or N replicas) each granted the
full window, and a restart cleared every bucket.  The bucket state now lives in
the database every service already shares.

Only rate-limit state is stored — client IP, capped/case-folded username and the
attempt timestamp.  No password, token or request body is written here, and the
append-only ``audit_events`` trail is untouched.

Forward-only: the table is additive, needs no backfill and is safe to apply to a
live database.  Re-runnable: both the table and its indexes are created only when
absent, so re-applying on an environment that already has them is a no-op.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd4b2c8e1f7a3'
down_revision: Union[str, Sequence[str], None] = 'b7c1e4d90a52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(connection, name: str) -> bool:
    return sa.inspect(connection).has_table(name)


def upgrade() -> None:
    connection = op.get_bind()
    if not _has_table(connection, 'login_attempts'):
        op.create_table(
            'login_attempts',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('client_ip', sa.String(45), nullable=False),
            sa.Column('username', sa.String(120), nullable=False),
            sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
    existing = {ix['name'] for ix in sa.inspect(connection).get_indexes('login_attempts')}
    if 'idx_login_attempts_key' not in existing:
        op.create_index('idx_login_attempts_key', 'login_attempts',
                        ['client_ip', 'username', 'attempted_at'])
    if 'idx_login_attempts_time' not in existing:
        op.create_index('idx_login_attempts_time', 'login_attempts', ['attempted_at'])


def downgrade() -> None:
    connection = op.get_bind()
    if _has_table(connection, 'login_attempts'):
        op.drop_table('login_attempts')
