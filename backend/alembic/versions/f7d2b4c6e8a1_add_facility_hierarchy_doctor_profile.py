"""add_facility_hierarchy_doctor_profile

Revision ID: f7d2b4c6e8a1
Revises: e6c1a9b3d5f8
Create Date: 2026-11-15

AMSDP-FACILITY-DOCTOR-01 — facility hierarchy, doctor profile, chamber sessions.

What this revision adds (all additive; no existing column is altered or dropped):

Facility hierarchy (service: organization)
    * ``facility_floors``       — per branch, optional
    * ``facility_departments``  — per branch, optional
    * ``facility_rooms``        — per branch, optional floor + optional department
    * ``specialties``           — org-owned structured speciality catalogue

Doctor profile (service: doctor)
    * ``doctors.bmdc_verification_status`` / ``bmdc_verified_at``
      (``doctors.registration_number`` already exists — it gains a policy)
    * ``doctors.photo_mime`` / ``photo_base64`` / ``photo_updated_at``
    * ``doctor_specialties``    — many-to-many doctor > speciality
    * ``doctor_branches``       — ``room_id``, ``consultation_fee_override``,
      ``is_primary``, ``status``, ``created_at``

Chamber sessions (service: scheduling)
    * ``schedule_sessions``     — where a doctor sits, per weekday window
    * ``appointments``          — ``session_id``, ``schedule_id`` and a
      *snapshot* of the chamber (``floor_id``/``floor_name``,
      ``department_id``/``department_name``, ``room_id``/``room_name``)

Why the snapshot columns (not just an FK)
-----------------------------------------
An appointment must keep showing the chamber it was booked into even after the
facility is reorganised, and a reprint of an old slip must not silently change.
The names are therefore copied at booking time; the ids remain for joins.

Double-booking safety
---------------------
``schedule_sessions`` carries two *partial* unique indexes so the database, not
only the service, refuses the same room — or the same doctor — starting two
active sessions at the same weekday minute::

    uq_session_room_start   (room_id, day_of_week, start_time)
                            WHERE room_id IS NOT NULL AND status = 'active'
    uq_session_doctor_start (doctor_id, day_of_week, start_time)
                            WHERE status = 'active'

Partial *overlaps* (09:00-13:00 vs 10:00-12:00) cannot be expressed this way
without ``btree_gist`` + an EXCLUDE constraint, which this deployment does not
have; the scheduling service refuses them inside a transaction that locks the
room row, which serialises concurrent writers.  These indexes are the backstop
for the exact-duplicate case that a race could still produce.

Backfill: none required.  New columns are nullable or carry a server default, so
existing rows stay valid and read as "not recorded" rather than as an error —
which is the documented behaviour when a branch has no facility model.

Re-runnable: every table, column, index and constraint is created only when
absent, so re-applying on an environment that already has it is a no-op.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7d2b4c6e8a1'
down_revision: Union[str, Sequence[str], None] = 'e6c1a9b3d5f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(connection, name: str) -> bool:
    return sa.inspect(connection).has_table(name)


def _columns(connection, table: str) -> set:
    if not _has_table(connection, table):
        return set()
    return {c['name'] for c in sa.inspect(connection).get_columns(table)}


def _indexes(connection, table: str) -> set:
    if not _has_table(connection, table):
        return set()
    return {ix['name'] for ix in sa.inspect(connection).get_indexes(table)
            if ix.get('name')}


def _add_column(connection, table: str, column: sa.Column) -> None:
    if column.name not in _columns(connection, table):
        op.add_column(table, column)


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()

    # -- facility hierarchy ---------------------------------------------------
    if not _has_table(connection, 'facility_floors'):
        op.create_table(
            'facility_floors',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('branch_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(120), nullable=False),
            sa.Column('code', sa.String(40), nullable=False),
            sa.Column('level', sa.Integer(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(20), nullable=True,
                      server_default='active'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True,
                      server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('branch_id', 'code', name='uq_floor_branch_code'),
        )
    for name, cols in (('idx_floor_branch', ['branch_id']),
                       ('idx_floor_org', ['organization_id'])):
        if name not in _indexes(connection, 'facility_floors'):
            op.create_index(name, 'facility_floors', cols)

    if not _has_table(connection, 'facility_departments'):
        op.create_table(
            'facility_departments',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('branch_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(120), nullable=False),
            sa.Column('code', sa.String(40), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(20), nullable=True,
                      server_default='active'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True,
                      server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('branch_id', 'code',
                                name='uq_department_branch_code'),
        )
    for name, cols in (('idx_department_branch', ['branch_id']),
                       ('idx_department_org', ['organization_id'])):
        if name not in _indexes(connection, 'facility_departments'):
            op.create_index(name, 'facility_departments', cols)

    if not _has_table(connection, 'facility_rooms'):
        op.create_table(
            'facility_rooms',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('branch_id', sa.String(), nullable=False),
            sa.Column('floor_id', sa.String(), nullable=True),
            sa.Column('department_id', sa.String(), nullable=True),
            sa.Column('name', sa.String(120), nullable=False),
            sa.Column('code', sa.String(40), nullable=False),
            sa.Column('room_type', sa.String(30), nullable=True,
                      server_default='consultation'),
            sa.Column('capacity', sa.Integer(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(20), nullable=True,
                      server_default='active'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True,
                      server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
            sa.ForeignKeyConstraint(['floor_id'], ['facility_floors.id']),
            sa.ForeignKeyConstraint(['department_id'], ['facility_departments.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('branch_id', 'code', name='uq_room_branch_code'),
        )
    for name, cols in (('idx_room_branch', ['branch_id']),
                       ('idx_room_floor', ['floor_id']),
                       ('idx_room_department', ['department_id']),
                       ('idx_room_org', ['organization_id'])):
        if name not in _indexes(connection, 'facility_rooms'):
            op.create_index(name, 'facility_rooms', cols)

    if not _has_table(connection, 'specialties'):
        op.create_table(
            'specialties',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('code', sa.String(50), nullable=False),
            sa.Column('name_en', sa.String(120), nullable=False),
            sa.Column('name_bn', sa.String(120), nullable=True,
                      server_default=''),
            sa.Column('sort_order', sa.Integer(), nullable=True,
                      server_default='0'),
            sa.Column('status', sa.String(20), nullable=True,
                      server_default='active'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True,
                      server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('organization_id', 'code',
                                name='uq_specialty_org_code'),
        )
    if 'idx_specialty_org' not in _indexes(connection, 'specialties'):
        op.create_index('idx_specialty_org', 'specialties', ['organization_id'])

    # -- doctor profile -------------------------------------------------------
    _add_column(connection, 'doctors', sa.Column(
        'bmdc_verification_status', sa.String(30), nullable=True,
        server_default='unverified'))
    _add_column(connection, 'doctors',
                sa.Column('bmdc_verified_at', sa.DateTime(timezone=True)))
    _add_column(connection, 'doctors', sa.Column('photo_mime', sa.String(40)))
    _add_column(connection, 'doctors', sa.Column('photo_base64', sa.Text()))
    _add_column(connection, 'doctors',
                sa.Column('photo_updated_at', sa.DateTime(timezone=True)))
    if 'idx_doctor_org_mobile' not in _indexes(connection, 'doctors'):
        op.create_index('idx_doctor_org_mobile', 'doctors',
                        ['organization_id', 'mobile'])

    if not _has_table(connection, 'doctor_specialties'):
        op.create_table(
            'doctor_specialties',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('doctor_id', sa.String(), nullable=False),
            sa.Column('specialty_id', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True,
                      server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id']),
            sa.ForeignKeyConstraint(['specialty_id'], ['specialties.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('doctor_id', 'specialty_id',
                                name='uq_doctor_specialty'),
        )
    if 'idx_doctor_specialty_doctor' not in _indexes(connection, 'doctor_specialties'):
        op.create_index('idx_doctor_specialty_doctor', 'doctor_specialties',
                        ['doctor_id'])

    # -- multi-branch assignment (existing table gains chamber + status) ------
    _add_column(connection, 'doctor_branches',
                sa.Column('room_id', sa.String(), nullable=True))
    _add_column(connection, 'doctor_branches',
                sa.Column('consultation_fee_override', sa.Float(), nullable=True))
    _add_column(connection, 'doctor_branches', sa.Column(
        'is_primary', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    _add_column(connection, 'doctor_branches', sa.Column(
        'status', sa.String(20), nullable=True, server_default='active'))
    _add_column(connection, 'doctor_branches', sa.Column(
        'created_at', sa.DateTime(timezone=True), nullable=True,
        server_default=sa.text('now()')))

    existing_fks = set()
    if _has_table(connection, 'doctor_branches'):
        existing_fks = {fk['name'] for fk in
                        sa.inspect(connection).get_foreign_keys('doctor_branches')}
    if 'fk_doctor_branches_room' not in existing_fks:
        op.create_foreign_key('fk_doctor_branches_room', 'doctor_branches',
                              'facility_rooms', ['room_id'], ['id'])
    if 'idx_doctor_branch_branch' not in _indexes(connection, 'doctor_branches'):
        op.create_index('idx_doctor_branch_branch', 'doctor_branches', ['branch_id'])
    # "At most one primary branch per doctor" — a fact, not a convention.
    if 'uq_doctor_one_primary' not in _indexes(connection, 'doctor_branches'):
        op.create_index('uq_doctor_one_primary', 'doctor_branches', ['doctor_id'],
                        unique=True, postgresql_where=sa.text('is_primary'))

    # -- chamber sessions -----------------------------------------------------
    if not _has_table(connection, 'schedule_sessions'):
        op.create_table(
            'schedule_sessions',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('branch_id', sa.String(), nullable=False),
            sa.Column('schedule_id', sa.String(), nullable=False),
            sa.Column('doctor_id', sa.String(), nullable=False),
            sa.Column('day_of_week', sa.Integer(), nullable=False),
            sa.Column('start_time', sa.String(5), nullable=False),
            sa.Column('end_time', sa.String(5), nullable=False),
            sa.Column('floor_id', sa.String(), nullable=True),
            sa.Column('department_id', sa.String(), nullable=True),
            sa.Column('room_id', sa.String(), nullable=True),
            sa.Column('slot_duration_minutes', sa.Integer(), nullable=True,
                      server_default='15'),
            sa.Column('max_patients', sa.Integer(), nullable=True,
                      server_default='1'),
            sa.Column('effective_from', sa.Date(), nullable=True),
            sa.Column('effective_to', sa.Date(), nullable=True),
            sa.Column('status', sa.String(20), nullable=True,
                      server_default='active'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True,
                      server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True,
                      server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
            sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id']),
            sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id']),
            sa.ForeignKeyConstraint(['floor_id'], ['facility_floors.id']),
            sa.ForeignKeyConstraint(['department_id'],
                                    ['facility_departments.id']),
            sa.ForeignKeyConstraint(['room_id'], ['facility_rooms.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('schedule_id', 'day_of_week', 'start_time',
                                name='uq_session_schedule_slot'),
        )
    for name, cols in (('idx_session_schedule', ['schedule_id']),
                       ('idx_session_room', ['room_id']),
                       ('idx_session_doctor', ['doctor_id']),
                       ('idx_session_org', ['organization_id'])):
        if name not in _indexes(connection, 'schedule_sessions'):
            op.create_index(name, 'schedule_sessions', cols)
    if 'uq_session_room_start' not in _indexes(connection, 'schedule_sessions'):
        op.create_index('uq_session_room_start', 'schedule_sessions',
                        ['room_id', 'day_of_week', 'start_time'], unique=True,
                        postgresql_where=sa.text(
                            "room_id IS NOT NULL AND status = 'active'"))
    if 'uq_session_doctor_start' not in _indexes(connection, 'schedule_sessions'):
        op.create_index('uq_session_doctor_start', 'schedule_sessions',
                        ['doctor_id', 'day_of_week', 'start_time'], unique=True,
                        postgresql_where=sa.text("status = 'active'"))

    # -- appointment location snapshot ---------------------------------------
    _add_column(connection, 'appointments',
                sa.Column('session_id', sa.String(), nullable=True))
    _add_column(connection, 'appointments',
                sa.Column('schedule_id', sa.String(), nullable=True))
    _add_column(connection, 'appointments',
                sa.Column('floor_id', sa.String(), nullable=True))
    _add_column(connection, 'appointments',
                sa.Column('floor_name', sa.String(120), nullable=True))
    _add_column(connection, 'appointments',
                sa.Column('department_id', sa.String(), nullable=True))
    _add_column(connection, 'appointments',
                sa.Column('department_name', sa.String(120), nullable=True))
    _add_column(connection, 'appointments',
                sa.Column('room_id', sa.String(), nullable=True))
    _add_column(connection, 'appointments',
                sa.Column('room_name', sa.String(120), nullable=True))

    appointment_fks = set()
    if _has_table(connection, 'appointments'):
        appointment_fks = {fk['name'] for fk in
                           sa.inspect(connection).get_foreign_keys('appointments')}
    for fk_name, column, target in (
            ('fk_appointments_session', 'session_id', 'schedule_sessions'),
            ('fk_appointments_schedule', 'schedule_id', 'schedules'),
            ('fk_appointments_floor', 'floor_id', 'facility_floors'),
            ('fk_appointments_department', 'department_id',
             'facility_departments'),
            ('fk_appointments_room', 'room_id', 'facility_rooms')):
        if fk_name not in appointment_fks:
            op.create_foreign_key(fk_name, 'appointments', target,
                                  [column], ['id'])
    if 'idx_appt_session' not in _indexes(connection, 'appointments'):
        op.create_index('idx_appt_session', 'appointments', ['session_id'])


def downgrade() -> None:
    """Downgrade schema — removes only what this revision added.

    Destructive by nature (the new tables hold the new data), which is why this
    revision is applied forward-only in practice.  Every step is guarded so a
    partial downgrade can be repeated safely.
    """
    connection = op.get_bind()

    for fk_name in ('fk_appointments_room', 'fk_appointments_department',
                    'fk_appointments_floor', 'fk_appointments_schedule',
                    'fk_appointments_session'):
        if _has_table(connection, 'appointments'):
            names = {fk['name'] for fk in
                     sa.inspect(connection).get_foreign_keys('appointments')}
            if fk_name in names:
                op.drop_constraint(fk_name, 'appointments', type_='foreignkey')
    for column in ('room_name', 'room_id', 'department_name', 'department_id',
                   'floor_name', 'floor_id', 'schedule_id', 'session_id'):
        if column in _columns(connection, 'appointments'):
            op.drop_column('appointments', column)

    if _has_table(connection, 'schedule_sessions'):
        op.drop_table('schedule_sessions')

    if _has_table(connection, 'doctor_branches'):
        names = {fk['name'] for fk in
                 sa.inspect(connection).get_foreign_keys('doctor_branches')}
        if 'fk_doctor_branches_room' in names:
            op.drop_constraint('fk_doctor_branches_room', 'doctor_branches',
                               type_='foreignkey')
        for column in ('created_at', 'status', 'is_primary',
                       'consultation_fee_override', 'room_id'):
            if column in _columns(connection, 'doctor_branches'):
                op.drop_column('doctor_branches', column)

    if _has_table(connection, 'doctor_specialties'):
        op.drop_table('doctor_specialties')

    for column in ('photo_updated_at', 'photo_base64', 'photo_mime',
                   'bmdc_verified_at', 'bmdc_verification_status'):
        if column in _columns(connection, 'doctors'):
            op.drop_column('doctors', column)

    for table in ('specialties', 'facility_rooms', 'facility_departments',
                  'facility_floors'):
        if _has_table(connection, table):
            op.drop_table(table)




