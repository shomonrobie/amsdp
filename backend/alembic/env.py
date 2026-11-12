from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
import os
import sys
# Ensure the backend directory is on sys.path so backend/common/ is importable
_here = os.path.dirname(os.path.abspath(__file__))          # backend/alembic
_backend_dir = os.path.dirname(_here)                        # backend/
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
from common.database import Base
# Import all models so they register with the Base metadata
from common import models  # noqa

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def _database_url() -> str:
    """Resolve the database URL from the environment.

    No credential is stored in ``alembic.ini``: the URL comes from
    ``AMSDP_DATABASE_URL``, the same variable docker compose, the ``_tools/``
    scripts and the services use (values live in the gitignored ``.env`` — see
    ``.env.example``).  Refusing to start is deliberate: a migration applied to
    the wrong database is far worse than a migration that will not run.
    """
    url = os.environ.get("AMSDP_DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError(
            "AMSDP_DATABASE_URL is not set and alembic.ini defines no "
            "sqlalchemy.url. Set AMSDP_DATABASE_URL (see .env.example) "
            "before running alembic."
        )
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # URL from the environment only — never from a committed ini value
    db_url = _database_url()
    config.set_main_option("sqlalchemy.url", db_url)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
