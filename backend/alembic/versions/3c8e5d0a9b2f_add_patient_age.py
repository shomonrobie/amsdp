"""add_patient_age

Revision ID: 3c8e5d0a9b2f
Revises: 9d8a1f2b3c4d
Create Date: 2026-11-08

Adds OPTIONAL reported `age` to patients (M7-B8).
- date_of_birth remains optional and is the authoritative source when present.
- age stores a patient's REPORTED age only (used when DOB is unknown/unwilling).
- A DOB is never inferred from a reported age; the two are independent.
- Existing rows keep working (nullable column).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c8e5d0a9b2f'
down_revision: Union[str, Sequence[str], None] = '9d8a1f2b3c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('patients', sa.Column('age', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('patients', 'age')