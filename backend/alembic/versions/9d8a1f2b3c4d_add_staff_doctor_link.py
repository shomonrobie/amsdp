"""add_staff_doctor_link

Revision ID: 9d8a1f2b3c4d
Revises: c7d3601e2486
Create Date: 2026-11-08

Adds an OPTIONAL staff<->doctor linkage column.
Every staff member is NOT a doctor; the link is nullable and must be
validated to reference a doctor in the same organization. Manual doctor
selection in the queue UI remains the fallback (BR §9 preserved).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d8a1f2b3c4d'
down_revision: Union[str, Sequence[str], None] = 'c7d3601e2486'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('staff_users', sa.Column('doctor_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_staff_users_doctor', 'staff_users', 'doctors',
                          ['doctor_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_staff_users_doctor', 'staff_users', type_='foreignkey')
    op.drop_column('staff_users', 'doctor_id')