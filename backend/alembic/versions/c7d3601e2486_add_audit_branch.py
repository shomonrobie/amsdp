"""add_audit_branch

Revision ID: c7d3601e2486
Revises: ccf34da72c1b
Create Date: 2026-11-08 14:14:29.720352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d3601e2486'
down_revision: Union[str, Sequence[str], None] = 'ccf34da72c1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('audit_events', sa.Column('branch_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_audit_events_branch', 'audit_events', 'branches', ['branch_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_audit_events_branch', 'audit_events', type_='foreignkey')
    op.drop_column('audit_events', 'branch_id')
