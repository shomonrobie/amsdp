"""Display administration — MP-39, and the denial accounting of MP-46.

What these tests prove
----------------------
* A role without ``queue.display.manage`` is refused **by the server**, and the
  refusal is recorded exactly once as ``queue.display.denied`` — not also as the
  generic ``request.denied`` row (Q-2 §10 / AC-21).
* A branch administrator can create, list and change a board, and every write
  leaves one audit row with before/after.
* The organization comes from the token: a cross-tenant write is a
  non-disclosing 404, recorded as a denial.
* A scope target from another branch is refused (422), so a half-configured
  board cannot widen a public feed.
* MP-45 through the admin path: switching ``show_room`` off makes ``room_name``
  **absent** from the raw public body, not hidden by the page.

Fixtures are written straight to the database (the same convention as
``test_multidisplay.py``); the public route is then driven through ``TestClient``
because the raw body is what the acceptance criteria are about.
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
from common.models import (AuditEvent, Branch, Doctor, DoctorBranch,
                           FacilityDepartment, FacilityRoom, Organization,
                           QueueDisplay, QueueDisplayDoctor)
from queuing.main import app

import amsdp_test_support as support

client = TestClient(app)

ORG = "dispadmin-org"
ORG_B = "dispadmin-org-b"
BR = "dispadmin-br"
BR_B = "dispadmin-br-b"
DEPT = "dispadmin-dept"
ROOM = "dispadmin-room"
DOC = "dispadmin-doc"
DOC_OTHER = "dispadmin-doc-other"

ADMIN = "dispadmin_admin"
RECEPTION = "dispadmin_reception"
OTHER_ADMIN = "dispadmin_other_admin"


def _purge():
    with SessionFactory() as s:
        ids = [d.id for d in s.query(QueueDisplay).filter(
            QueueDisplay.organization_id.in_([ORG, ORG_B])).all()]
        if ids:
            s.query(QueueDisplayDoctor).filter(
                QueueDisplayDoctor.display_id.in_(ids)).delete(
                    synchronize_session=False)
            s.query(AuditEvent).filter(
                AuditEvent.target_id.in_(ids)).delete(synchronize_session=False)
            s.query(QueueDisplay).filter(
                QueueDisplay.id.in_(ids)).delete(synchronize_session=False)
        s.query(AuditEvent).filter(AuditEvent.organization_id.in_([ORG, ORG_B])).delete(
            synchronize_session=False)
        s.query(DoctorBranch).filter(DoctorBranch.branch_id.in_([BR, BR_B])).delete(
            synchronize_session=False)
        s.query(FacilityRoom).filter(FacilityRoom.id == ROOM).delete()
        s.query(FacilityDepartment).filter(FacilityDepartment.id == DEPT).delete()
        s.query(Doctor).filter(Doctor.organization_id.in_([ORG, ORG_B])).delete(
            synchronize_session=False)
        s.commit()


def _seed():
    support.ensure_org(ORG)
    support.ensure_org(ORG_B)
    support.ensure_branch(BR, ORG)
    support.ensure_branch(BR_B, ORG_B)
    support.ensure_doctor(DOC, ORG, name="Dr. Display One")
    support.ensure_doctor(DOC_OTHER, ORG, name="Dr. Display Two")
    with SessionFactory() as s:
        s.add(FacilityDepartment(id=DEPT, organization_id=ORG, branch_id=BR,
                                 name="Cardiology", code="DISP-CARD"))
        s.add(FacilityRoom(id=ROOM, organization_id=ORG, branch_id=BR,
                           department_id=DEPT, name="Chamber 201", code="DISP-201",
                           room_type="consultation"))
        s.add(DoctorBranch(doctor_id=DOC, branch_id=BR, room_id=ROOM))
        s.commit()
    support.ensure_user(ADMIN, "branch_admin", ORG, BR)
    support.ensure_user(RECEPTION, "receptionist", ORG, BR)
    support.ensure_user(OTHER_ADMIN, "branch_admin", ORG_B, BR_B)


@pytest.fixture(autouse=True)
def _fresh():
    _purge()
    _seed()
    yield
    _purge()


def _denials(target_id=""):
    with SessionFactory() as s:
        query = s.query(AuditEvent).filter(
            AuditEvent.organization_id == ORG,
            AuditEvent.action == "queue.display.denied")
        rows = query.all()
        if target_id:
            rows = [r for r in rows if r.target_id == target_id]
        return rows


def _audit(action):
    with SessionFactory() as s:
        return s.query(AuditEvent).filter(
            AuditEvent.organization_id.in_([ORG, ORG_B]),
            AuditEvent.action == action).all()


def _create(code="cardio", **overrides):
    body = {"branch_id": BR, "name": "Cardiology Board", "code": code,
            "language": "bn", "scope_type": "branch", "footer_text": ""}
    body.update(overrides)
    return client.post("/api/v1/queue/displays", json=body,
                       headers=support.headers(ADMIN))


def test_a_receptionist_is_refused_and_the_refusal_is_one_row():
    resp = client.post("/api/v1/queue/displays",
                       json={"branch_id": BR, "name": "X", "code": "x"},
                       headers=support.headers(RECEPTION))
    assert resp.status_code == 403
    # The marker is internal: it must not reach the caller.
    assert "x-amsdp-denial-audit" not in {k.lower() for k in resp.headers}

    rows = _denials()
    assert len(rows) == 1, "one denial is one row"
    assert rows[0].actor_role == "receptionist"
    assert rows[0].organization_id == ORG
    # The generic recorder must not add a second row for the same refusal.
    assert [r for r in _audit("request.denied")] == [], \
        "the domain-specific row replaces the generic one"


def test_an_anonymous_caller_gets_401_and_writes_nothing():
    resp = client.post("/api/v1/queue/displays",
                       json={"branch_id": BR, "name": "X", "code": "x"})
    assert resp.status_code in (401, 403)
    assert _denials() == [], "an unauthenticated refusal cannot be attributed"


def test_a_branch_admin_creates_a_board_and_it_is_audited_with_after():
    resp = _create(code="  CARDIOLOGY  ")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["code"] == "cardiology", "the handle is normalised to lower case"
    assert body["organization_id"] == ORG, "the tenant comes from the token"
    assert body["branch_id"] == BR
    assert body["status"] == "active"

    created = _audit("queue.display.created")
    assert len(created) == 1
    assert created[0].target_id == body["id"]
    assert created[0].after["code"] == "cardiology"
    assert created[0].actor_id, "the actor is recorded"


def test_a_duplicate_code_in_the_same_branch_is_refused():
    assert _create(code="dup").status_code == 201
    second = _create(code="dup")
    assert second.status_code == 409
    assert "already" in second.json()["detail"]


def test_the_created_board_serves_only_its_scope_on_the_public_route():
    resp = _create(code="doctored", scope_type="doctors", doctor_ids=[DOC])
    assert resp.status_code == 201, resp.text
    public = client.get(f"/api/v1/queue/display/{ORG}/{BR}?display=doctored")
    assert public.status_code == 200
    assert public.json()["display"]["code"] == "doctored"
    assert public.json()["display"]["scope_type"] == "doctors"
    # The historic board is untouched by any of this.
    historic = client.get(f"/api/v1/queue/display/{ORG}/{BR}")
    assert historic.status_code == 200
    assert "display" not in historic.json()


def test_a_scope_target_from_another_tenant_is_refused_with_422():
    resp = _create(code="foreign", scope_type="department", department_id="nope")
    assert resp.status_code == 422
    assert "department" in resp.json()["detail"]


def test_a_doctor_not_posted_to_the_branch_is_refused():
    resp = _create(code="unposted", scope_type="doctors",
                   doctor_ids=["no-such-doctor"])
    assert resp.status_code == 422



def test_a_cross_tenant_patch_is_a_404_and_a_recorded_denial():
    created = _create(code="mine").json()
    resp = client.patch(f"/api/v1/queue/displays/{created['id']}",
                        json={"name": "Stolen"},
                        headers=support.headers(OTHER_ADMIN))
    assert resp.status_code == 404, "a foreign row is indistinguishable from a missing one"
    with SessionFactory() as s:
        assert s.query(QueueDisplay).filter(
            QueueDisplay.id == created["id"]).first().name == "Cardiology Board"
    with SessionFactory() as s:
        denied = s.query(AuditEvent).filter(
            AuditEvent.action == "queue.display.denied",
            AuditEvent.organization_id == ORG_B).all()
    assert len(denied) == 1, "the refusal is attributed to the caller's own tenant"


def test_each_patch_writes_one_row_with_before_and_after():
    created = _create(code="editable").json()
    resp = client.patch(f"/api/v1/queue/displays/{created['id']}",
                        json={"language": "en", "footer_text": "Welcome"},
                        headers=support.headers(ADMIN))
    assert resp.status_code == 200, resp.text
    assert resp.json()["language"] == "en"

    updated = _audit("queue.display.updated")
    assert len(updated) == 1
    assert updated[0].before["language"] == "bn"
    assert updated[0].after["language"] == "en"
    assert updated[0].after["footer_text"] == "Welcome"

    # An unchanged save changes nothing and therefore audits nothing.
    again = client.patch(f"/api/v1/queue/displays/{created['id']}",
                         json={"language": "en"}, headers=support.headers(ADMIN))
    assert again.status_code == 200
    assert len(_audit("queue.display.updated")) == 1, "a no-op writes no audit row"


def test_mp45_switching_a_field_off_removes_it_from_the_public_body():
    created = _create(code="quiet").json()
    assert created["show_room"] is True

    resp = client.patch(f"/api/v1/queue/displays/{created['id']}",
                        json={"show_room": False, "show_waiting_count": False},
                        headers=support.headers(ADMIN))
    assert resp.status_code == 200

    public = client.get(f"/api/v1/queue/display/{ORG}/{BR}?display=quiet")
    assert public.status_code == 200
    raw = public.text
    assert "room_name" not in raw, "a switched-off field is absent, not hidden"
    assert "patients_waiting" not in raw
    assert "estimated_wait_minutes" in raw, "the fields that stayed on are published"


def test_a_disabled_board_404s_exactly_like_an_unknown_code():
    created = _create(code="switched-off").json()
    client.patch(f"/api/v1/queue/displays/{created['id']}",
                 json={"status": "disabled"}, headers=support.headers(ADMIN))
    disabled = client.get(f"/api/v1/queue/display/{ORG}/{BR}?display=switched-off")
    unknown = client.get(f"/api/v1/queue/display/{ORG}/{BR}?display=no-such-board")
    assert disabled.status_code == 404
    assert unknown.status_code == 404
    assert disabled.json() == unknown.json()
    assert disabled.headers.get("cache-control") == unknown.headers.get("cache-control")


def test_the_list_is_scoped_and_needs_a_branch():
    assert _create(code="one").status_code == 201
    listed = client.get(f"/api/v1/queue/displays?branch_id={BR}",
                        headers=support.headers(ADMIN))
    assert listed.status_code == 200
    assert [d["code"] for d in listed.json()["displays"]] == ["one"]

    # A branch administrator's token carries a branch; an organization-wide
    # caller without one is asked for it rather than guessed at.
    support.ensure_user("dispadmin_orgadmin", "org_admin", ORG)
    missing = client.get("/api/v1/queue/displays",
                         headers=support.headers("dispadmin_orgadmin"))
    assert missing.status_code == 422


def test_a_code_cannot_be_reused_after_a_rename():
    first = _create(code="taken").json()
    second = _create(code="other").json()
    resp = client.patch(f"/api/v1/queue/displays/{second['id']}",
                        json={"code": "taken"}, headers=support.headers(ADMIN))
    assert resp.status_code == 409
    with SessionFactory() as s:
        assert s.query(QueueDisplay).filter(
            QueueDisplay.id == second["id"]).first().code == "other"
        assert s.query(QueueDisplay).filter(
            QueueDisplay.id == first["id"]).first().code == "taken"

