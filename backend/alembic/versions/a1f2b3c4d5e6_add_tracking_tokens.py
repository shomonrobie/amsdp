"""add_tracking_tokens

Revision ID: a1f2b3c4d5e6
Revises: 3c8e5d0a9b2f
Create Date: 2026-11-09

PQT tracking token table (M9-B). Stores only the token hash and prefix;
the raw token is never persisted. The UNIQUE index on token_hash enables
O(1) lookup without iteration.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1f2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '3c8e5d0a9b2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tracking_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('appointment_id', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('token_prefix', sa.String(8), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('eligible_at', sa.DateTime(timezone=True)),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appointment_id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index('ix_tracking_tokens_hash', 'tracking_tokens', ['token_hash'])


def downgrade() -> None:
    op.drop_table('tracking_tokens')