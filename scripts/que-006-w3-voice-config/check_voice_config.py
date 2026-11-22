"""Execute the pure QUE-006/W3 voice-configuration tests without pytest.

Why this exists
---------------
This verification host has Python 3.13 but no ``pytest``, no ``fastapi``, no
``sqlalchemy`` and no PostgreSQL, so ``backend/organization/tests/test_voice_packs_api.py``
cannot run here.  ``backend/organization/tests/test_voice_pack_policy.py`` however
is *pure*: it imports only the standard library and
``organization.voice_pack_policy``, which in turn imports only
``common.permissions`` (itself dependency-free).  This runner loads that module
and calls every ``test_*`` function, so the permission matrix, the precedence
rule, the lifecycle refusals and the upload checks are genuinely executed rather
than merely described in a report.

It is not a substitute for pytest: on a host with ``pytest`` installed, run
``pytest backend/organization/tests/test_voice_pack_policy.py`` and prefer that
result.

Usage::

    python scripts/que-006-w3-voice-config/check_voice_config.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BACKEND = os.path.join(ROOT, "backend")
MODULE_PATH = os.path.join(BACKEND, "organization", "tests",
                           "test_voice_pack_policy.py")


def _load_module():
    if BACKEND not in sys.path:
        sys.path.insert(0, BACKEND)
    spec = importlib.util.spec_from_file_location("test_voice_pack_policy",
                                                  MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = _load_module()
    names = sorted(n for n in dir(module)
                   if n.startswith("test_") and callable(getattr(module, n)))
    passed = failed = 0
    for name in names:
        try:
            getattr(module, name)()
        except Exception:
            failed += 1
            print("FAIL " + name)
            traceback.print_exc()
        else:
            passed += 1
            print("PASS " + name)
    print("---")
    print(f"{len(names)} tests, {passed} pass, {failed} fail")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
