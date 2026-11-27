"""Collection purity — importing the suite must not touch a database.

Why this module exists
----------------------
Finding **T-10** (27 November 2026): seven test modules created reference rows
*at import time*, so pytest's **collection** phase wrote to whichever database
``AMSDP_DATABASE_URL`` pointed at.  Two things were wrong with that, and only one
of them was about the database:

* a read-only command (`--collect-only`) mutated state — a fact about the suite
  rather than about any test in it;
* the suite was order-dependent without saying so.  ``tests/test_security.py``
  seeded ``other-org-999`` before a single test ran, which is precisely why a
  cross-tenant defect (**D-3**) passed in every whole-tree run and failed when
  its module was run alone.

The import-time writes are gone (register §19.3).  This module is the guard that
keeps them gone — and it needs **no database**, which is what makes it runnable
in a window that is not authorised to touch one: it points the suite at a
sentinel DSN that cannot be reached and requires collection to succeed anyway.
Reintroduce import-time seeding and the subprocess cannot collect, so this test
fails with the traceback attached.

Two assertions, deliberately separate:

1. **the sentinel really is unreachable** — the negative control.  Without it the
   second assertion would be vacuous (a sentinel that answered would let an
   import-time write succeed).
2. **collection completes with the sentinel in place** — the invariant itself.

Both run in a subprocess, so the parent process's own configuration cannot mask a
regression.  Nothing here asserts product behaviour and nothing connects to a
database: the only connection attempt in the file is the one deliberately made to
a closed port.
"""

import os
import pathlib
import re
import subprocess
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]

# Port 1 (tcpmux) is reserved and nothing listens on it, so the attempt is
# refused at the socket immediately rather than timing out.  The database name is
# a label, not a target — it exists on no server.
SENTINEL_URL = "postgresql+psycopg2://amsdp@127.0.0.1:1/amsdp_collection_guard"

# A floor, not a fixed count: the suite grows, and this guard must not fail
# because a module was added.  It exists to catch collection collapsing to
# nothing — which is what an import-time failure looks like from the outside.
MIN_EXPECTED_TESTS = 1000

# Opens one connection through the application's own session factory and exits 0
# only when that connection is refused.
_PROBE = """
import sys
sys.path.insert(0, ".")
from sqlalchemy import text
from common.database import SessionFactory

session = SessionFactory()
try:
    session.execute(text("select 1"))
except Exception as exc:            # the exception type is the assertion
    print(type(exc).__name__)
    print(exc)
    raise SystemExit(0)
raise SystemExit("the sentinel database accepted a connection")
"""


def _run(args, *, timeout):
    """Run a child process against the sentinel DSN, from the backend root."""
    env = dict(os.environ)
    env["AMSDP_DATABASE_URL"] = SENTINEL_URL
    return subprocess.run(
        args,
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_the_sentinel_dsn_is_unreachable():
    """Negative control: if this fails, the collection check proves nothing."""
    result = _run([sys.executable, "-c", _PROBE], timeout=120)
    output = result.stdout + result.stderr
    assert result.returncode == 0, (
        "the sentinel DSN must be unreachable; a reachable sentinel would let an "
        "import-time write succeed and make the collection guard vacuous:\n"
        + output[-2000:]
    )
    assert "OperationalError" in result.stdout, (
        "the connection attempt must fail as a PostgreSQL operational error:\n"
        + output[-2000:]
    )


def test_collection_succeeds_with_no_reachable_database():
    """T-10: collecting the suite must not require — or touch — a database."""
    result = _run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "-p", "no:cacheprovider"],
        timeout=600,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, (
        "collection must succeed with the sentinel database in place; a non-zero "
        "exit means some module touched the database at import time (T-10):\n"
        + output[-3000:]
    )
    assert "OperationalError" not in output, (
        "a connection was attempted during collection:\n" + output[-3000:]
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match, "collection did not report a count:\n" + output[-2000:]
    assert int(match.group(1)) >= MIN_EXPECTED_TESTS, (
        "collection produced %s tests, below the expected floor of %d — the suite "
        "has collapsed rather than merely shrunk:\n%s"
        % (match.group(1), MIN_EXPECTED_TESTS, output[-2000:])
    )
