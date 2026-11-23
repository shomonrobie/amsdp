"""add_voice_packs_and_platform_announcement_config

Revision ID: c4d8e2a91f60
Revises: a7c3f19d2b64
Create Date: 2026-11-21

QUE-006 / W3: versioned voice packs and the platform announcement defaults.

Two additive tables, nothing else:

``voice_packs``
    one row per *version* of one voice persona, platform-wide (``organization_id``
    NULL) or belonging to one organisation.  ``voice_name`` groups the versions of
    a persona, so the next version is always ``max + 1``; a published row is never
    overwritten, which is what keeps rollback possible.
    ``available_to_organizations`` is the platform's release switch for a
    published platform pack.

``announcement_platform_config``
    the platform defaults (language, default English pack, default Bangla pack).
    An organisation's override lives in the existing ``organizations.config`` JSON
    block and therefore needs no schema change.

Parent revision note
--------------------
``down_revision`` is ``a7c3f19d2b64`` (the QUE-006/W2 delivery-claim table), the
newest revision present in this working tree.  That revision currently declares
``down_revision = 'f8a2b3c4d5e6'`` instead of the true head ``a9c4e1f7b2d8``,
which creates a second Alembic head; the defect is recorded in
``docs/implementation/QUE-006_W2_PRE_COMMIT_REVIEW_REPORT.md`` and is *not* fixed
here (W2 is out of this task's scope).  Once W2's revision is reparented to
``a9c4e1f7b2d8`` this migration follows it correctly with no further change.  If
W2's revision is dropped instead, set ``down_revision = 'a9c4e1f7b2d8'``.

Forward-only and idempotent: each table and index is created only when absent, so
re-running against a database that already has them is a no-op.  No existing
table, column, constraint or row is modified.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4d8e2a91f60'
down_revision: Union[str, Sequence[str], None] = 'a7c3f19d2b64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PACKS = 'voice_packs'
PLATFORM = 'announcement_platform_config'


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not inspector.has_table(PACKS):
        op.create_table(
            PACKS,
            sa.Column('id', sa.String(length=80), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=True),
            sa.Column('language', sa.String(length=8), nullable=False),
            sa.Column('voice_name', sa.String(length=80), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('personality', sa.String(length=80), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False,
                      server_default='1'),
            sa.Column('status', sa.String(length=24), nullable=False,
                      server_default='draft'),
            sa.Column('base_path', sa.String(length=200), nullable=True),
            sa.Column('manifest', sa.JSON(), nullable=True),
            sa.Column('manifest_checksum', sa.String(length=64), nullable=True),
            sa.Column('compatibility', sa.JSON(), nullable=True),
            sa.Column('available_to_organizations', sa.Boolean(),
                      nullable=False, server_default=sa.false()),
            sa.Column('validation_status', sa.String(length=16),
                      nullable=False, server_default='unvalidated'),
            sa.Column('validation_problems', sa.JSON(), nullable=True),
            sa.Column('validated_at', sa.DateTime(timezone=True),
                      nullable=True),
            sa.Column('review_status', sa.String(length=16), nullable=False,
                      server_default='pending'),
            sa.Column('reviewed_by', sa.String(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('review_note', sa.Text(), nullable=True),
            sa.Column('published_by', sa.String(), nullable=True),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
            sa.UniqueConstraint(
                'organization_id', 'language', 'voice_name', 'version',
                name='voice_packs_scope_language_voice_version_key'),
        )

    existing = {ix['name'] for ix in inspector.get_indexes(PACKS)}
    if 'idx_voice_packs_scope_language' not in existing:
        op.create_index('idx_voice_packs_scope_language', PACKS,
                        ['organization_id', 'language'])
    if 'idx_voice_packs_status' not in existing:
        op.create_index('idx_voice_packs_status', PACKS, ['status'])

    if not inspector.has_table(PLATFORM):
        op.create_table(
            PLATFORM,
            sa.Column('id', sa.String(length=20), nullable=False),
            sa.Column('language', sa.String(length=8), nullable=False,
                      server_default='bn'),
            sa.Column('voice_packs', sa.JSON(), nullable=True),
            sa.Column('updated_by', sa.String(), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if inspector.has_table(PLATFORM):
        op.drop_table(PLATFORM)

    if inspector.has_table(PACKS):
        existing = {ix['name'] for ix in inspector.get_indexes(PACKS)}
        if 'idx_voice_packs_status' in existing:
            op.drop_index('idx_voice_packs_status', table_name=PACKS)
        if 'idx_voice_packs_scope_language' in existing:
            op.drop_index('idx_voice_packs_scope_language', table_name=PACKS)
        op.drop_table(PACKS)
