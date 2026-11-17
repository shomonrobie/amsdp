"""add_symptom_catalogue

Revision ID: b3d7e91f6a24
Revises: f7d2b4c6e8a1
Create Date: 2026-11-16

AMSDP-SYMPTOM-01 — bilingual patient-reported symptom catalogue, appointment
symptom records and the optional onset question.

What this revision adds (all additive; no existing column is altered or dropped)
-------------------------------------------------------------------------------
Symptoms (service: appointment)
    * ``symptom_catalog``      — org-owned bilingual catalogue: code, English and
      Bangla names, English/Bangla synonyms, category, speciality *ranking
      hints*, source, review status, sort order, active/inactive
    * ``appointment_symptoms`` — one row per recorded symptom.  Two shapes share
      the table because the distinction must survive in the record:
      ``kind='catalogue'`` (FK + name snapshot) and ``kind='free_text'``
      (receptionist's own words).  ``text_key`` is the duplicate-suppression key.

Onset (service: appointment)
    * ``appointments.symptom_onset_code`` — closed vocabulary (TODAY … UNKNOWN),
      never a forced date
    * ``appointments.symptom_onset_note`` — optional short free note

Why a snapshot and not just a join
----------------------------------
``appointment_symptoms.name_en``/``name_bn`` copy the catalogue wording at
booking time.  A catalogue entry that is renamed, re-categorised or retired
must not rewrite what a receptionist recorded for a visit that already
happened — the same rule the chamber snapshot on ``appointments`` follows
(revision ``f7d2b4c6e8a1``).  ``symptom_id`` is kept for joins and provenance.

Duplicate safety
----------------
Two *partial* unique indexes make the database, not only the service, the last
line of defence::

    uq_appt_symptom_catalogue (appointment_id, symptom_id)
                              WHERE symptom_id IS NOT NULL
    uq_appt_symptom_text      (appointment_id, text_key)
                              WHERE symptom_id IS NULL AND text_key <> ''

``ck_appt_symptom_shape`` additionally forbids a row that claims to be a
catalogue entry without an id, or free text without text, so the two shapes can
never be conflated by a future writer.

Backfill: none required.  The new columns are nullable and the catalogue starts
empty for an organization that has never seeded one; a booking made before (or
without) the catalogue simply records no symptoms, which is the documented
behaviour of an optional field.

Re-runnable: every table, column, index and constraint is created only when
absent, so re-applying on an environment that already has it is a no-op.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3d7e91f6a24'
down_revision: Union[str, Sequence[str], None] = 'f7d2b4c6e8a1'
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
    return {i['name'] for i in sa.inspect(connection).get_indexes(table)}




def _add_column(connection, table: str, column: sa.Column) -> None:
    """Add ``column`` to ``table`` only when it is not there yet."""
    if not _has_table(connection, table):
        return
    if column.name in _columns(connection, table):
        return
    op.add_column(table, column)


def upgrade() -> None:
    connection = op.get_bind()

    # --- symptom_catalog ----------------------------------------------------
    if not _has_table(connection, 'symptom_catalog'):
        op.create_table(
            'symptom_catalog',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('organization_id', sa.String(),
                      sa.ForeignKey('organizations.id'), nullable=False),
            sa.Column('code', sa.String(60), nullable=False),
            sa.Column('name_en', sa.String(160), nullable=False),
            sa.Column('name_bn', sa.String(160), nullable=True, server_default=''),
            sa.Column('synonyms_en', sa.JSON(), nullable=True),
            sa.Column('synonyms_bn', sa.JSON(), nullable=True),
            sa.Column('category', sa.String(60), nullable=True,
                      server_default='general'),
            sa.Column('specialty_hints', sa.JSON(), nullable=True),
            sa.Column('source', sa.String(300), nullable=True, server_default=''),
            sa.Column('review_status', sa.String(30), nullable=True,
                      server_default='unreviewed'),
            sa.Column('sort_order', sa.Integer(), nullable=True, server_default='100'),
            sa.Column('status', sa.String(20), nullable=True, server_default='active'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint('organization_id', 'code',
                                name='uq_symptom_org_code'),
        )
    catalog_indexes = _indexes(connection, 'symptom_catalog')
    if 'idx_symptom_org' not in catalog_indexes:
        op.create_index('idx_symptom_org', 'symptom_catalog', ['organization_id'])
    if 'idx_symptom_org_status' not in catalog_indexes:
        op.create_index('idx_symptom_org_status', 'symptom_catalog',
                        ['organization_id', 'status'])

    # --- appointment_symptoms ----------------------------------------------
    if not _has_table(connection, 'appointment_symptoms'):
        op.create_table(
            'appointment_symptoms',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('organization_id', sa.String(),
                      sa.ForeignKey('organizations.id'), nullable=False),
            sa.Column('appointment_id', sa.String(),
                      sa.ForeignKey('appointments.id'), nullable=False),
            sa.Column('kind', sa.String(20), nullable=False),
            sa.Column('symptom_id', sa.String(),
                      sa.ForeignKey('symptom_catalog.id'), nullable=True),
            sa.Column('name_en', sa.String(160), nullable=False,
                      server_default=''),
            sa.Column('name_bn', sa.String(160), nullable=False,
                      server_default=''),
            sa.Column('text_reported', sa.Text(), nullable=False,
                      server_default=''),
            sa.Column('text_key', sa.String(300), nullable=False,
                      server_default=''),
            sa.Column('recorded_by', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint(
                "(kind = 'catalogue' AND symptom_id IS NOT NULL"
                " AND length(trim(text_reported)) = 0)"
                " OR (kind = 'free_text' AND symptom_id IS NULL"
                " AND length(trim(text_reported)) > 0)",
                name='ck_appt_symptom_shape'),
        )
    symptom_indexes = _indexes(connection, 'appointment_symptoms')
    if 'idx_appt_symptom_appt' not in symptom_indexes:
        op.create_index('idx_appt_symptom_appt', 'appointment_symptoms',
                        ['appointment_id'])
    if 'idx_appt_symptom_org' not in symptom_indexes:
        op.create_index('idx_appt_symptom_org', 'appointment_symptoms',
                        ['organization_id'])
    if 'uq_appt_symptom_catalogue' not in symptom_indexes:
        op.create_index('uq_appt_symptom_catalogue', 'appointment_symptoms',
                        ['appointment_id', 'symptom_id'], unique=True,
                        postgresql_where=sa.text('symptom_id IS NOT NULL'))
    if 'uq_appt_symptom_text' not in symptom_indexes:
        op.create_index('uq_appt_symptom_text', 'appointment_symptoms',
                        ['appointment_id', 'text_key'], unique=True,
                        postgresql_where=sa.text(
                            "symptom_id IS NULL AND text_key <> ''"))

    # --- onset on the appointment ------------------------------------------
    _add_column(connection, 'appointments',
                sa.Column('symptom_onset_code', sa.String(30), nullable=True))
    _add_column(connection, 'appointments',
                sa.Column('symptom_onset_note', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema — removes only what this revision added.

    Destructive by nature (the symptom rows hold the recorded complaints), which
    is why this revision is applied forward-only in practice.  Every step is
    guarded so a partial downgrade can be repeated safely.
    """
    connection = op.get_bind()

    for column in ('symptom_onset_note', 'symptom_onset_code'):
        if column in _columns(connection, 'appointments'):
            op.drop_column('appointments', column)

    if _has_table(connection, 'appointment_symptoms'):
        op.drop_table('appointment_symptoms')

    if _has_table(connection, 'symptom_catalog'):
        op.drop_table('symptom_catalog')
