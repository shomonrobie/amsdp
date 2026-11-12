"""Placeholder package — **not** a deployment entry point (SEQ4-DEPLOY-D1).

AMSDP has no aggregate backend app.  The runtime is the eight per-service
FastAPI applications (``identity``, ``organization``, ``patient``, ``doctor``,
``scheduling``, ``appointment``, ``queuing``, ``audit``), each built from its own
Dockerfile and wired to the browser through the Next.js proxy in
``frontend/next.config.js``.  ``docker-compose.yml`` deliberately builds none of
this module.

Nothing here serves ``/api/v1/...``.  Deploying ``app.main:app`` would answer
``GET /`` with ``Hello World`` and 404 every real route, which is why it stays a
stub instead of growing into a second, divergent copy of the service routers.
"""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World"}
