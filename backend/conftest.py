"""pytest bootstrap for the AMSDP backend suite.

The suite lives in two places: ``backend/tests/`` (cross-service tests) and each
service's own ``<service>/tests/`` directory.  Both need the backend package root
on ``sys.path`` (``common.*``, the service packages) and the shared helper module
``tests/amsdp_test_support.py``.  Doing it here, once, replaces the per-file
``sys.path.insert`` dance — and it is what lets the rewritten service tests use
the same seeding/auth helpers instead of each re-deriving fixtures.

Nothing here changes application behaviour: no environment variable is set, no
fixture monkeypatches product code, and the database URL still comes from
``AMSDP_DATABASE_URL`` (``common/database.py``) so the suite can be pointed at a
throwaway database.
"""

import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_TESTS_DIR = os.path.join(_BACKEND_DIR, "tests")

for _path in (_BACKEND_DIR, _TESTS_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)
