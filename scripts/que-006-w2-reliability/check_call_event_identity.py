"""Execute the pure queue call-event tests without pytest.

Why this exists
---------------
The W2 verification host has Python 3.13 but no ``pytest``, no ``fastapi`` and
no PostgreSQL, so ``backend/queuing/tests/test_queue.py`` cannot run here.
``backend/queuing/tests/test_queue_events.py`` however is *pure* — it imports
only ``os``, ``sys`` and ``queuing.events``. This runner loads that module and
calls every ``test_*`` function, so the identity rule is genuinely executed
rather than merely described in a report.

It is not a substitute for pytest: on a host with ``pytest`` installed, run
``pytest backend/queuing/tests/test_queue_events.py`` and prefer that result.

Usage::

    python scripts/que-006-w2-reliability/check_call_event_identity.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BACKEND = os.path.join(ROOT, "backend")
MODULE_PATH = os.path.join(BACKEND, "queuing", "tests", "test_queue_events.py")


def _load_module():
    if BACKEND not in sys.path:
        sys.path.insert(0, BACKEND)
    spec = importlib.util.spec_from_file_location("test_queue_events", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = _load_module()
    names = sorted(n for n in dir(module) if n.startswith("test_") and callable(getattr(module, n)))
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
