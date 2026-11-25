"""MP-05 — the demo seed's operational day and doctor scope.

Two defects this file pins:

* **GAP-03 / GAP-25 (day).** ``seed_demo`` filed the demo week and today's queue
  under ``date.today()`` — the *container's* date.  At 01:00 Dhaka that is
  yesterday, so a re-seed produced a queue nobody could see on the board and a
  week that started a day early.  The seed now asks the facility (BR §8).
* **PO-RBAC-01 (scope).** No ``staff_doctor_assignments`` row was seeded at all.
  ``common.auth._load_assigned_doctor_ids`` reads only that table and refuses the
  legacy ``staff_users.doctor_id`` fallback once the table exists, so the seeded
  doctor login could reach no doctor's queue — the demo path failed closed.

The live re-seed is **not** performed by this test: it runs against whatever
``AMSDP_DATABASE_URL`` points at (the disposable scratch database) and the seed
is idempotent, so running it twice is itself part of the assertion.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, datetime, timezone

import common.timeutil as timeutil
from common.auth import AuthContext, _load_assigned_doctor_ids
from common.database import SessionFactory
from common.models import StaffDoctorAssignment, StaffUser
from seed import seed_demo

DEMO_ORG_ID = seed_demo.DEMO_ORG["id"]
DEMO_DOCTOR_ID = "demo-dr-002"
OTHER_DOCTOR_ID = "demo-dr-001"


def test_demo_today_is_the_facility_day_not_the_server_day(monkeypatch):
    """2026-11-23T19:00Z is 01:00 on the 24th in Dhaka — the seed must say 24."""
    fixed_utc = datetime(2026, 11, 23, 19, 0, tzinfo=timezone.utc)

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_utc.astimezone(tz) if tz else fixed_utc.replace(tzinfo=None)

    class _ServerDate(date):
        @classmethod
        def today(cls):
            return date(2026, 11, 23)

    monkeypatch.setattr(timeutil, "datetime", _FrozenDateTime)
    # Inert after the fix; if the seed reads the server clock again it answers
    # the 23rd and the assertion fails.
    monkeypatch.setattr(seed_demo, "date", _ServerDate, raising=False)

    session = SessionFactory()
    try:
        assert seed_demo._demo_today(session) == date(2026, 11, 24)
    finally:
        session.close()


def test_seed_calls_no_server_local_date():
    """No `X.today()` call may remain anywhere in the seed module."""
    src = open(seed_demo.__file__, encoding="utf-8").read()
    offending = [
        node.lineno for node in ast.walk(ast.parse(src))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "today"
    ]
    assert offending == [], f"server-local date read at line(s) {offending}"


def test_seed_assigns_exactly_one_doctor_to_the_doctor_and_assistant(monkeypatch):
    """The seeded doctor and assistant each hold one active assignment."""
    # A placeholder, not a credential: the seed's password source is stubbed so
    # this test never depends on (or writes) a real demo password.
    monkeypatch.setattr(seed_demo, "_demo_password",
                        lambda username: "seed-test-placeholder")
    seed_demo.seed()
    seed_demo.seed()             # idempotent: the second run adds nothing

    session = SessionFactory()
    try:
        for username in ("doctor", "assistant"):
            user = session.query(StaffUser).filter(
                StaffUser.username == username,
                StaffUser.organization_id == DEMO_ORG_ID).first()
            assert user is not None, f"seeded staff '{username}' is missing"
            active = session.query(StaffDoctorAssignment).filter(
                StaffDoctorAssignment.staff_user_id == user.id,
                StaffDoctorAssignment.status == "active").all()
            assert len(active) == 1, (
                f"'{username}' holds {len(active)} active assignments, expected 1")
            assert active[0].doctor_id == DEMO_DOCTOR_ID
            assert active[0].organization_id == DEMO_ORG_ID

            # The scope the auth layer will actually load, and what it permits.
            assigned = _load_assigned_doctor_ids(session, user.id)
            assert assigned == [DEMO_DOCTOR_ID], assigned
            ctx = AuthContext(user_id=user.id, organization_id=DEMO_ORG_ID,
                              branch_id=user.branch_id, role=user.role,
                              username=user.username, locale=user.locale or "bn",
                              status=user.status or "active", token_payload={},
                              assigned_doctor_ids=assigned)
            assert ctx.can_access_doctor(DEMO_DOCTOR_ID) is True
            assert ctx.can_access_doctor(OTHER_DOCTOR_ID) is False
    finally:
        session.close()
