"""The organisation service must import in the layout the *image* uses.

Why this file exists (acceptance-readiness verification, 2026-11-23)
--------------------------------------------------------------------
``organization/Dockerfile`` builds ``organization/`` into ``/app`` and starts
``uvicorn main:app``.  In that layout ``main.py`` is a **top-level** module, so
``from . import voice_pack_policy`` raises *attempted relative import with no
known parent package* while the service is importing — the container is dead on
arrival.  Every unit test still passed, because ``load_app("organization")``
imports ``organization.main`` as a *package*, where relative imports resolve.

That is the worst kind of defect: invisible to the suite and fatal in
production.  This test therefore re-imports the service the way the image does,
in a subprocess so the two layouts can never shadow each other's SQLAlchemy
models, and asserts that the app and the W3 routers are actually mounted.
"""

import os
import subprocess
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
ORG_DIR = os.path.join(BACKEND_DIR, "organization")

_FLAT_IMPORT = r"""
import sys

# Exactly the layout inside the image: /app = the organization/ directory.
sys.path.insert(0, {org_dir!r})
sys.path.insert(0, {backend_dir!r})          # for `common.*`

import main                                   # noqa: E402  (flat, like uvicorn)

# FastAPI (0.162) keeps an included router as an opaque `_IncludedRouter` entry
# in `app.routes`, so walking `.path` would miss every mounted router.  The
# OpenAPI schema is the honest answer to "is this router really mounted?" — and
# building it also proves every route's signature still resolves.
paths = main.app.openapi()["paths"]
assert "/api/v1/voice-packs" in paths, sorted(paths)
assert any(p.startswith("/api/v1/voice-packs/") for p in paths), sorted(paths)
assert any("announcement-config" in p for p in paths), sorted(paths)
print("FLAT_IMPORT_OK")
"""


def test_the_service_imports_in_the_flat_container_layout():
    """`uvicorn main:app` must work: no unguarded relative imports in the image."""
    code = _FLAT_IMPORT.format(org_dir=ORG_DIR, backend_dir=BACKEND_DIR)
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ORG_DIR,
        capture_output=True,
        text=True,
        timeout=180,
        env={**os.environ, "PYTHONPATH": ""},
    )
    assert completed.returncode == 0, (
        "the organization service cannot be imported in the container layout:\n"
        f"stdout={completed.stdout}\nstderr={completed.stderr}"
    )
    assert "FLAT_IMPORT_OK" in completed.stdout, completed.stdout
