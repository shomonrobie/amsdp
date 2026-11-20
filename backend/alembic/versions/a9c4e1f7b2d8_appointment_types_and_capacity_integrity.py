"""appointment_types_and_capacity_integrity

Revision ID: a9c4e1f7b2d8
Revises: b3d7e91f6a24, f8a2b3c4d5e6
Create Date: 2026-11-19

Owner decisions Q1, Q2, Q4 (AMSDP-APPT-OWNER-DECISIONS-01).

Three changes, forward-only and idempotent:

1. ``appointments.override_reason`` — why an outside-session ("unscheduled")
   appointment was accepted.  Existing rows are **not** rewritten: they keep
   their type and simply carry no override reason, because they never needed an
   override.  Nothing is inferred from a missing ``start_time``.

2. ``slot_allocations`` — the database capacity guarantee (Q2).  One row per
   claimed seat, uniquely numbered inside its slot.  ``UNIQUE (doctor_id,
   appointment_date, slot_key, seat_number)`` allows capacity-N slots while
   making a duplicate seat impossible; ``UNIQUE (appointment_id)`` makes a
   double claim impossible.  Live appointments are backfilled so the guarantee
   covers the rows that already exist.

   Backfill caveat, stated plainly: the seat key is the appointment's stored
   ``start_time`` (a published window start is not derivable in SQL — it comes
   from the doctor's templates).  For rows booked at a window start the key is
   exactly the runtime key; for a 09:07 booking of the 09:00 window it is
   ``09:07``.  Those historical rows are therefore *not* deduplicated against
   the 09:00 window by the constraint — the application's count guard still
   charges them to the window.  Capacity overruns that already exist are
   **reported, never repaired** (see the NOTICE below).

3. ``staff_capability_grants`` — Q4's explicitly granted, independently
   revocable, optionally branch-scoped capability.

Rollback: dropping the two tables loses allocation and grant *history*, not
appointments or staff rows.  Re-running the upgrade rebuilds the allocations
from the surviving appointments, but a revoked/then-dropped grant cannot be
reconstructed — which is why the downgrade is documented rather than promised.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a9c4e1f7b2d8'
down_revision: Union[str, Sequence[str], None] = ('b3d7e91f6a24',
                                                 'f8a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#: Appointment statuses that occupy a seat (mirrors
#: ``appointment.main.APPOINTMENT_ACTIVE_STATUSES``).
ACTIVE_STATUSES = ('BOOKED', 'AWAITING_CONFIRMATION', 'CONFIRMED',
                   'CHECKED_IN', 'IN_QUEUE')

#: ``slot_allocations.slot_key`` for the outside-session pool.
UNSCHEDULED_SLOT_KEY = 'UNSCHEDULED'


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # --- 1. appointments.override_reason -----------------------------------
    columns = {col['name'] for col in inspector.get_columns('appointments')}
    if 'override_reason' not in columns:
        op.add_column('appointments',
                      sa.Column('override_reason', sa.String(length=200),
                                nullable=True))

    # --- 2. slot_allocations ----------------------------------------------
    if not inspector.has_table('slot_allocations'):
        op.create_table(
            'slot_allocations',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('doctor_id', sa.String(), nullable=False),
            sa.Column('appointment_date', sa.Date(), nullable=False),
            sa.Column('slot_key', sa.String(length=20), nullable=False),
            sa.Column('slot_end', sa.String(length=10), nullable=True),
            sa.Column('kind', sa.String(length=20), nullable=False,
                      server_default='scheduled'),
            sa.Column('seat_number', sa.Integer(), nullable=False),
            sa.Column('appointment_id', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'],
                                    ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('doctor_id', 'appointment_date', 'slot_key',
                                'seat_number', name='uq_slot_allocation_seat'),
            sa.UniqueConstraint('appointment_id',
                                name='uq_slot_allocation_appointment'),
        )
        op.create_index('idx_slot_allocation_lookup', 'slot_allocations',
                        ['doctor_id', 'appointment_date', 'slot_key'])
        op.create_index('idx_slot_allocation_org', 'slot_allocations',
                        ['organization_id'])

    # --- 2b. backfill live appointments, and report overruns ---------------
    _backfill_allocations(connection)
    _report_capacity_inconsistencies(connection)

    # --- 3. staff_capability_grants ---------------------------------------
    if not inspector.has_table('staff_capability_grants'):
        op.create_table(
            'staff_capability_grants',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('staff_user_id', sa.String(), nullable=False),
            sa.Column('capability', sa.String(length=60), nullable=False),
            sa.Column('branch_id', sa.String(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False,
                      server_default='active'),
            sa.Column('granted_by', sa.String(), nullable=True),
            sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('revoked_by', sa.String(), nullable=True),
            sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('reason', sa.String(length=200), nullable=True),
            sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
            sa.ForeignKeyConstraint(['staff_user_id'], ['staff_users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('staff_user_id', 'capability', 'branch_id',
                                name='uq_staff_capability_grant'),
        )
        # PostgreSQL treats NULLs as distinct, so the constraint above does not
        # stop a second organization-wide grant of the same capability.
        op.create_index('uq_staff_capability_grant_orgwide',
                        'staff_capability_grants',
                        ['staff_user_id', 'capability'], unique=True,
                        postgresql_where=sa.text('branch_id IS NULL'))
        op.create_index('idx_staff_capability_staff', 'staff_capability_grants',
                        ['staff_user_id'])
        op.create_index('idx_staff_capability_org', 'staff_capability_grants',
                        ['organization_id'])



def _backfill_allocations(connection) -> None:
    """Give every live appointment the seat it already occupies.

    Idempotent: an appointment that already has an allocation is skipped, so a
    re-run adds nothing.  Seat numbers are dense (1..n) within each key, which is
    exactly what the runtime claim does for new bookings.
    """
    rows = connection.execute(sa.text("""
        SELECT a.id, a.organization_id, a.doctor_id, a.appointment_date,
               a.start_time, a.appointment_type
        FROM appointments a
        WHERE a.status IN :statuses
          AND NOT EXISTS (SELECT 1 FROM slot_allocations sa
                          WHERE sa.appointment_id = a.id)
        ORDER BY a.doctor_id, a.appointment_date, a.start_time, a.created_at, a.id
    """).bindparams(sa.bindparam('statuses', expanding=True)),
        {"statuses": list(ACTIVE_STATUSES)}).fetchall()

    import uuid
    from datetime import datetime, timezone

    seats: dict = {}
    now = datetime.now(timezone.utc)
    for appt_id, org_id, doctor_id, day, start_time, appt_type in rows:
        slot_key = start_time or UNSCHEDULED_SLOT_KEY
        key = (doctor_id, day, slot_key)
        seat = seats.get(key, 0) + 1
        seats[key] = seat
        kind = (appt_type if appt_type in ('scheduled', 'walk_in', 'unscheduled')
                else 'scheduled')
        connection.execute(sa.text("""
            INSERT INTO slot_allocations
                (id, organization_id, doctor_id, appointment_date, slot_key,
                 slot_end, kind, seat_number, appointment_id, created_at)
            VALUES (:id, :oid, :did, :day, :slot_key, NULL, :kind, :seat,
                    :appt_id, :created_at)
        """), {"id": str(uuid.uuid4()), "oid": org_id, "did": doctor_id,
               "day": day, "slot_key": slot_key, "kind": kind,
               "seat": seat, "appt_id": appt_id, "created_at": now})


def _report_capacity_inconsistencies(connection) -> None:
    """Report — never repair — slots that already hold more than one patient.

    The exact capacity is a function of the doctor's templates, which SQL cannot
    read here, so the check is the conservative one a migration *can* make: more
    than one live appointment at the same doctor, day and minute.  A capacity-N
    template legitimately allows that once published, so these rows are reported
    for an operator to review rather than treated as errors.  Nothing is deleted,
    merged or rewritten.
    """
    import logging

    rows = connection.execute(sa.text("""
        SELECT doctor_id, appointment_date, start_time, COUNT(*) AS booked
        FROM appointments
        WHERE status IN :statuses
          AND start_time IS NOT NULL
        GROUP BY doctor_id, appointment_date, start_time
        HAVING COUNT(*) > 1
        ORDER BY booked DESC
        LIMIT 20
    """).bindparams(sa.bindparam('statuses', expanding=True)),
        {"statuses": list(ACTIVE_STATUSES)}).fetchall()
    log = logging.getLogger("alembic.runtime.migration")
    if not rows:
        log.info("slot capacity review: no duplicate-minute bookings found")
        return
    log.warning("slot capacity review: %d doctor/day/minute group(s) hold more "
                "than one live appointment; review against the published "
                "templates (nothing was changed)", len(rows))
    for doctor_id, day, start_time, booked in rows:
        log.warning("  doctor=%s date=%s start=%s live=%s",
                    doctor_id, day, start_time, booked)


def downgrade() -> None:
    """Downgrade schema.

    Documented limitation: this drops allocation and grant rows.  Appointments
    and staff users are untouched, so no business record is lost, but the record
    of *which seat* an appointment held and *who held which capability* is.
    """
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if inspector.has_table('staff_capability_grants'):
        op.drop_index('idx_staff_capability_org',
                      table_name='staff_capability_grants')
        op.drop_index('idx_staff_capability_staff',
                      table_name='staff_capability_grants')
        op.drop_index('uq_staff_capability_grant_orgwide',
                      table_name='staff_capability_grants')
        op.drop_table('staff_capability_grants')

    if inspector.has_table('slot_allocations'):
        op.drop_index('idx_slot_allocation_org', table_name='slot_allocations')
        op.drop_index('idx_slot_allocation_lookup',
                      table_name='slot_allocations')
        op.drop_table('slot_allocations')

    columns = {col['name'] for col in
               sa.inspect(connection).get_columns('appointments')}
    if 'override_reason' in columns:
        op.drop_column('appointments', 'override_reason')
