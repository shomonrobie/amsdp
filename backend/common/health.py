"""Liveness and readiness endpoints shared by every backend service.

Sequence 4 finding SEQ4-DEPLOY-D2: nothing in the stack could tell whether a
service was actually up, so ``docker compose`` had no application-tier start
order and an orchestrator (compose, Render, k8s) had no way to restart a wedged
container.  M8 §12 lists ``/health`` endpoints as an M8-D item; this module is
that item, installed identically by all eight services.

Two endpoints, deliberately separate:

``GET /health``
    Liveness only — the process is running and its ASGI app responds.  It must
    not touch the database: a database outage is not a reason to restart a web
    process, and restarting one would only add connection churn.

``GET /health/ready``
    Readiness — the service can serve requests, which for AMSDP means the shared
    PostgreSQL is reachable (``SELECT 1``).  Compose gates dependent services on
    this, so a container is only wired into the network once it can answer.

Both are unauthenticated by design (a healthcheck cannot hold a token) and leak
nothing but the service name: no tenant ids, no version strings, no DSN, no
error detail from the database.
"""

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from .database import engine


def install_health(app: FastAPI, service: str) -> None:
    """Register ``/health`` and ``/health/ready`` on *app* for *service*."""

    @app.get("/health", include_in_schema=False)
    def health():                                            # noqa: D401
        return {"status": "ok", "service": service}

    @app.get("/health/ready", include_in_schema=False)
    def health_ready():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:
            # Never echo the driver error: it can contain host/user/db names.
            raise HTTPException(503, "database unavailable")
        return {"status": "ready", "service": service}
