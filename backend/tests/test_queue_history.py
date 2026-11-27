"""Queue history — MP-24, asserted against the route itself.

Why this module exists
----------------------
`frontend/pages/queue-history.js` consumes `/api/v1/queue/history`, and until
this file existed the route was only ever asserted from the frontend's *source
scan* (`frontend/tests/queue-history.test.mjs` reads the page text).  A source
scan cannot fail when the route's own scope rules break, so MP-24's acceptance —
*"branch-scoped; cross-branch returns 404; history survives completion"* — was
untested at the place it is enforced.

What these tests prove
----------------------
* Every status is returned for the doctor and day, **including `completed`**, so
  history outlives the entry's terminal state (the point of the screen).
* `status=` narrows without re-classifying anything.
* A `branch_id` outside the caller's authority is the *same* non-disclosing 404
  as a branch that does not exist — the response body and status are compared,
  not just the code.
* With no `branch_id`, a branch-scoped caller is confined to the branch in the
  token; the other branch of the same organization stays invisible.
* A doctor's or assistant's own history is the only history they can read.
* An unparseable date is a 422, never a 500 or an unfiltered scan.

Fixtures are written straight to the database (the same convention as
``test_display_admin.py`` and ``test_multidisplay.py``).
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "queuing"))

from datetime import date

import pytest
from fastapi.testclient import TestClient

from common.database import SessionFactory
from common.models import QueueEntry
from queuing.main import app

import amsdp_test_support as support

client = TestClient(app)

ORG = "qhist-org"
ORG_B = "qhist-org-b"
BR = "qhist-br"
BR2 = "qhist-br-2"
BR_B = "qhist-br-b"
DOC = "qhist-doc"
DOC_B = "qhist-doc-b"
PAT = "qhist-pat"
PAT2 = "qhist-pat-2"

ADMIN = "qhist_admin"
DOCTOR_USER = "qhist_doctor"

DAY = date(2026, 11, 27)


def _seed():
    support.ensure_org(ORG)
    support.ensure_org(ORG_B)
    support.ensure_branch(BR, ORG)
    support.ensure_branch(BR2, ORG)
    support.ensure_branch(BR_B, ORG_B)
    support.ensure_doctor(DOC, ORG, name="Dr. History")
    support.ensure_doctor(DOC_B, ORG_B, name="Dr. Other Tenant")
    support.ensure_patient(PAT, ORG, name="Patient One")
    support.ensure_patient(PAT2, ORG, name="Patient Two")
    support.ensure_user(ADMIN, "branch_admin", ORG, BR)
    support.ensure_user(DOCTOR_USER, "doctor", ORG, BR)


def _entry(*, branch_id, doctor_id, status, position, token, patient_id=PAT):
    with SessionFactory() as s:
        s.add(QueueEntry(id=str(uuid.uuid4()), organization_id=ORG,
                         branch_id=branch_id, doctor_id=doctor_id, date=DAY,
                         position=position, token=token, patient_id=patient_id,
                         status=status, status_history=[],
                         position_history=[]))
        s.commit()


@pytest.fixture(autouse=True)
def _fresh():
    support.purge_org(ORG)
    support.purge_org(ORG_B)
    _seed()
    # One entry per interesting state, plus a second `completed` entry so the
    # status filter is proved to narrow rather than to return everything.
    _entry(branch_id=BR, doctor_id=DOC, status="waiting", position=1, token="A-001")
    _entry(branch_id=BR, doctor_id=DOC, status="called", position=2, token="A-002")
    _entry(branch_id=BR, doctor_id=DOC, status="completed", position=3,
           token="A-003", patient_id=PAT2)
    _entry(branch_id=BR, doctor_id=DOC, status="completed", position=4, token="A-004")
    _entry(branch_id=BR2, doctor_id=DOC, status="waiting", position=1, token="B-001")
    yield
    support.purge_org(ORG)
    support.purge_org(ORG_B)


def _history(**params):
    query = {"doctor_id": DOC, "date": DAY.isoformat()}
    query.update({k: v for k, v in params.items() if v is not None})
    return client.get("/api/v1/queue/history", params=query,
                      headers=support.headers(ADMIN))


def _tokens(resp):
    return [row["token"] for row in resp.json()]


def test_history_returns_every_status_including_completed():
    resp = _history()
    assert resp.status_code == 200, resp.text
    # The branch-scoped administrator sees their own branch only (four entries),
    # and a completed consultation is still history.
    assert _tokens(resp) == ["A-001", "A-002", "A-003", "A-004"]
    assert "completed" in {row["status"] for row in resp.json()}, \
        "history survives completion — that is the screen's whole purpose"


def test_the_status_filter_narrows_without_re_classifying():
    resp = _history(status="completed")
    assert resp.status_code == 200, resp.text
    assert _tokens(resp) == ["A-003", "A-004"]
    assert {row["status"] for row in resp.json()} == {"completed"}


def test_a_foreign_branch_is_the_same_404_as_a_missing_one():
    foreign = _history(branch_id=BR_B)          # another organisation's branch
    missing = _history(branch_id="qhist-no-such-branch")
    assert foreign.status_code == 404
    assert missing.status_code == 404
    # Non-disclosing: an existing branch the caller may not use is
    # indistinguishable from one that does not exist.
    assert foreign.json() == missing.json()


def test_a_branch_scoped_caller_is_confined_to_the_token_branch():
    own = _history(branch_id=BR)
    assert own.status_code == 200
    assert _tokens(own) == ["A-001", "A-002", "A-003", "A-004"]
    # Without the parameter the token's branch still applies, so the other
    # branch of the same organisation (B-001) never appears.
    implicit = _history()
    assert "B-001" not in _tokens(implicit)


def test_another_branch_of_the_same_tenant_is_refused_not_narrowed():
    # BR2 belongs to the caller's organisation, yet the caller's token is scoped
    # to BR: the request is refused, so the caller cannot mistake another
    # branch's silence for data.
    resp = _history(branch_id=BR2)
    assert resp.status_code == 404


def test_a_doctor_reads_only_their_own_history():
    # No staff_doctor_assignment exists for this login, and the route fails
    # closed rather than defaulting to the requested doctor.
    resp = client.get("/api/v1/queue/history",
                      params={"doctor_id": DOC, "date": DAY.isoformat()},
                      headers=support.headers(DOCTOR_USER))
    assert resp.status_code == 404


def test_an_invalid_date_is_a_422():
    resp = client.get("/api/v1/queue/history",
                      params={"doctor_id": DOC, "date": "27-11-2026"},
                      headers=support.headers(ADMIN))
    assert resp.status_code == 422
    assert "date" in resp.json()["detail"]


def test_another_tenants_doctor_yields_no_rows():
    # Org scoping is applied to the query, so a foreign doctor id cannot be
    # used to read another tenant's entries; it simply matches nothing.
    resp = client.get("/api/v1/queue/history",
                      params={"doctor_id": DOC_B, "date": DAY.isoformat()},
                      headers=support.headers(ADMIN))
    assert resp.status_code == 200
    assert resp.json() == []
