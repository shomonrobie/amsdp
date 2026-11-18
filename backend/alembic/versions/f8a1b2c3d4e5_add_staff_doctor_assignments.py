"""add_staff_doctor_assignments

Revision ID: f8a1b2c3d4e5
Revises: e6c1a9b3d5f8
Create Date: 2026-11-17

PO-RBAC-01: Introduce explicit staff->doctor assignment table so an assistant
may be assigned to multiple doctors within the same organization.

The legacy StaffUser.doctor_id column is preserved as a compatibility field.
Existing doctor_id values on staff_users are backfilled into the new table so
no existing assignment is lost.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f8a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = 'e6c1a9b3d5f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Create the assignment table only if it does not already exist (idempotent).
    if not inspector.has_table('staff_doctor_assignments'):
        op.create_table(
            'staff_doctor_assignments',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('staff_user_id', sa.String(), nullable=False),
            sa.Column('doctor_id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=False, server_default='active'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
            sa.ForeignKeyConstraint(['staff_user_id'], ['staff_users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('staff_user_id', 'doctor_id',
                                name='uq_staff_doctor_assignment'),
        )
        op.create_index(
            'idx_staff_doctor_assignment_staff',
            'staff_doctor_assignments', ['staff_user_id'],
        )
        op.create_index(
            'idx_staff_doctor_assignment_doctor',
            'staff_doctor_assignments', ['doctor_id'],
        )
        op.create_index(
            'idx_staff_doctor_assignment_org',
            'staff_doctor_assignments', ['organization_id'],
        )

    # Backfill existing StaffUser.doctor_id values as active assignments.
    # Only for staff whose role is assistant or doctor, and whose doctor_id
    # references a doctor in the same organization.  Done in Python so we can
    # generate UUIDs portably without relying on pgcrypto.
    if inspector.has_table('staff_users') and inspector.has_table('doctors'):
        import uuid
        from datetime import datetime, timezone
        rows = connection.execute(sa.text("""
            SELECT su.id, su.doctor_id, su.organization_id, su.created_at
            FROM staff_users su
            JOIN doctors d ON d.id = su.doctor_id AND d.organization_id = su.organization_id
            WHERE su.doctor_id IS NOT NULL
              AND su.role IN ('assistant', 'doctor')
        """)).fetchall()
        now = datetime.now(timezone.utc).isoformat()
        for staff_user_id, doctor_id, organization_id, created_at in rows:
            # Skip if already assigned (idempotent re-run)
            existing = connection.execute(sa.text("""
                SELECT 1 FROM staff_doctor_assignments
                WHERE staff_user_id = :sid AND doctor_id = :did
                LIMIT 1
            """), {"sid": staff_user_id, "did": doctor_id}).fetchone()
            if existing:
                continue
            connection.execute(sa.text("""
                INSERT INTO staff_doctor_assignments
                    (id, staff_user_id, doctor_id, organization_id, status, created_at)
                VALUES (:id, :sid, :did, :oid, 'active', :cat)
            """), {
                "id": str(uuid.uuid4()),
                "sid": staff_user_id,
                "did": doctor_id,
                "oid": organization_id,
                "cat": created_at.isoformat() if hasattr(created_at, 'isoformat') else now,
            })


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Restore legacy doctor_id for staff who had exactly one active assignment.
    # Staff with multiple assignments keep only the most recent.
    if inspector.has_table('staff_doctor_assignments'):
        op.execute("""
            UPDATE staff_users su
            SET doctor_id = sda.doctor_id
            FROM (
                SELECT DISTINCT ON (staff_user_id) staff_user_id, doctor_id
                FROM staff_doctor_assignments
                WHERE status = 'active'
                ORDER BY staff_user_id, created_at DESC
            ) sda
            WHERE su.id = sda.staff_user_id
              AND su.doctor_id IS DISTINCT FROM sda.doctor_id
        """)

        op.drop_index('idx_staff_doctor_assignment_org',
                      table_name='staff_doctor_assignments')
        op.drop_index('idx_staff_doctor_assignment_doctor',
                      table_name='staff_doctor_assignments')
        op.drop_index('idx_staff_doctor_assignment_staff',
                      table_name='staff_doctor_assignments')
        op.drop_table('staff_doctor_assignments')