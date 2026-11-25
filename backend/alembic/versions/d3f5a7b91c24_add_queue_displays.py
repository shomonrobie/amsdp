"""add_queue_displays

Revision ID: d3f5a7b91c24
Revises: b2e5c7d91a04
Create Date: 2026-11-25

MP-35 / MP-37 / MP-41 / MP-45 — the multi-display DQDS registry.

Two **additive** tables and nothing else:

``queue_displays``
    one row per configured public board: which doctors it shows
    (``scope_type``), in which language, which optional public fields it may
    publish (``show_room`` / ``show_estimated_wait`` / ``show_waiting_count``),
    its footer and its lifecycle.  ``(branch_id, code)`` is unique because the
    code is the public handle in ``?display=<code>``.
``queue_display_doctors``
    membership for ``scope_type='doctors'``; the composite primary key makes a
    duplicate membership impossible.

Why one revision creates the whole table
----------------------------------------
MP-35, MP-37, MP-41 and MP-45 each own *behaviour* (department scope, room
scope, publication policy), but all of that state lives as columns on a table
that does not exist yet.  Creating a table and then immediately altering it
twice would add three irreversible steps where one will do, and a half-applied
chain would leave a display with no way to express "this field is off".  One
revision therefore creates the complete table once; the tasks are delivered and
evidenced by the resolver, the payload and their tests.

Deliberately unchanged
----------------------
No existing table, column, constraint, index or row is touched.  In particular
``queue_entries`` gains no room column: the room *label* is a read through
``doctor_branches.room_id → facility_rooms``, per specification §5.1 item 5.

Forward-only and idempotent: every object is created only when absent, so a
second ``upgrade head`` on the same database is a no-op.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd3f5a7b91c24'
down_revision: Union[str, Sequence[str], None] = 'b2e5c7d91a04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DISPLAYS = 'queue_displays'


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not inspector.has_table(DISPLAYS):
        op.create_table(
            DISPLAYS,
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('branch_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('code', sa.String(length=40), nullable=False),
            sa.Column('language', sa.String(length=2), nullable=False,
                      server_default='bn'),
            sa.Column('scope_type', sa.String(length=20), nullable=False,
                      server_default='branch'),
            sa.Column('department_id', sa.String(), nullable=True),
            sa.Column('room_id', sa.String(), nullable=True),
            sa.Column('footer_text', sa.String(length=160), nullable=False,
                      server_default=''),
            sa.Column('show_room', sa.Boolean(), nullable=False,
                      server_default=sa.text('true')),
            sa.Column('show_estimated_wait', sa.Boolean(), nullable=False,
                      server_default=sa.text('true')),
            sa.Column('show_waiting_count', sa.Boolean(), nullable=False,
                      server_default=sa.text('true')),
            sa.Column('status', sa.String(length=20), nullable=False,
                      server_default='active'),
            sa.Column('created_by', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
            sa.ForeignKeyConstraint(['department_id'], ['facility_departments.id']),
            sa.ForeignKeyConstraint(['room_id'], ['facility_rooms.id']),
            sa.ForeignKeyConstraint(['created_by'], ['staff_users.id']),
            sa.UniqueConstraint('branch_id', 'code', name='uq_display_branch_code'),
            sa.CheckConstraint(
                "scope_type IN ('branch', 'doctors', 'department', 'room')",
                name='ck_display_scope_type'),
            sa.CheckConstraint("language IN ('bn', 'en')",
                               name='ck_display_language'),
            sa.CheckConstraint("status IN ('active', 'disabled')",
                               name='ck_display_status'),
            # A scope without its target would silently fall back to the whole
            # branch.  Refused by the database, not only by the service.
            sa.CheckConstraint(
                "scope_type <> 'department' OR department_id IS NOT NULL",
                name='ck_display_department_scope'),
            sa.CheckConstraint("scope_type <> 'room' OR room_id IS NOT NULL",
                               name='ck_display_room_scope'),
        )

    if not inspector.has_table(DISPLAY_DOCTORS):
        op.create_table(
            DISPLAY_DOCTORS,
            sa.Column('display_id', sa.String(), nullable=False),
            sa.Column('doctor_id', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('display_id', 'doctor_id'),
            sa.ForeignKeyConstraint(['display_id'], [f'{DISPLAYS}.id']),
            sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id']),
        )

    existing = {ix['name'] for ix in inspector.get_indexes(DISPLAYS)}
    if 'idx_display_branch' not in existing:
        op.create_index('idx_display_branch', DISPLAYS, ['branch_id'])
    if 'idx_display_org' not in existing:
        op.create_index('idx_display_org', DISPLAYS, ['organization_id'])

    existing = {ix['name'] for ix in inspector.get_indexes(DISPLAY_DOCTORS)}
    if 'idx_display_doctor_doctor' not in existing:
        op.create_index('idx_display_doctor_doctor', DISPLAY_DOCTORS, ['doctor_id'])


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if inspector.has_table(DISPLAY_DOCTORS):
        existing = {ix['name'] for ix in inspector.get_indexes(DISPLAY_DOCTORS)}
        if 'idx_display_doctor_doctor' in existing:
            op.drop_index('idx_display_doctor_doctor', table_name=DISPLAY_DOCTORS)
        op.drop_table(DISPLAY_DOCTORS)

    if inspector.has_table(DISPLAYS):
        existing = {ix['name'] for ix in inspector.get_indexes(DISPLAYS)}
        for name in ('idx_display_org', 'idx_display_branch'):
            if name in existing:
                op.drop_index(name, table_name=DISPLAYS)
        op.drop_table(DISPLAYS)

DISPLAY_DOCTORS = 'queue_display_doctors'
