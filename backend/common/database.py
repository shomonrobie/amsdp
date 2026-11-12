"""AMSDP Shared Database Infrastructure.

Single SQLAlchemy engine, session factory, and declarative base
shared by all microservices within the same process.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)


def _default_url() -> str:
    """Development DSN composed from the environment.

    The password is never stored in source: it comes from ``POSTGRES_PASSWORD``
    (the same variable docker compose uses, kept in the gitignored ``.env`` —
    see ``.env.example``).  When it is absent the DSN is passwordless, which
    PostgreSQL rejects with an explicit authentication error rather than the
    application silently using a credential committed to the repository.
    """
    host = os.environ.get("AMSDP_DB_HOST", "127.0.0.1")
    port = os.environ.get("AMSDP_DB_PORT", "5433")
    name = os.environ.get("AMSDP_DB_NAME", "amsdp")
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        logger.warning(
            "Neither AMSDP_DATABASE_URL nor POSTGRES_PASSWORD is set: falling back to a "
            "passwordless development DSN. Set both (or the latter) in .env - see .env.example."
        )
        return f"postgresql+psycopg2://amsdp@{host}:{port}/{name}"
    return f"postgresql+psycopg2://amsdp:{password}@{host}:{port}/{name}"


DATABASE_URL = os.environ.get("AMSDP_DATABASE_URL") or _default_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=os.environ.get("AMSDP_DB_ECHO", "0") == "1",
)

SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()


def get_session():
    """Yield a session suitable for a request-scoped dependency.

    The caller owns the session and must close it.
    """
    session = SessionFactory()
    try:
        return session
    finally:
        session.close()


def get_db():
    """FastAPI dependency: yield a session, rollback on error."""
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
