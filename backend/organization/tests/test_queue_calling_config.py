"""Tests for the organization doctor queue-calling policy (QUE-006 / DEV-1).

Owner decision D: whether a doctor may call their own patient forward is an
organization setting, enforced server-side by the queuing service.  This module
covers the *organization* half — the effective value, the default derived from
the facility type, the write permission, tenant scoping and the audit record.
The enforcement half is covered in ``backend/queuing/tests/test_queue.py``
(``TestDoctorQueueCalling``).
"""

import pytest
from fastapi.testclient import TestClient

import common.config as config
from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                               ensure_user, headers, load_app, purge_org, uniq)
from common.config import get_queue_calling_config
from common.models import AuditEvent, Organization

ORG = "qcc-org"
BR = "qcc-branch"
OTHER_ORG = "qcc-other-org"
OTHER_BR = "qcc-other-branch"
ADMIN = "qcc_admin"
OTHER_ADMIN = "qcc_other_admin"
DOCTOR = "qcc_doctor"
RECP = "qcc_recp"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("organization"))


@pytest.fixture(autouse=True)
def _world(client):
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_user(ADMIN, "org_admin", ORG, BR)
    ensure_user(OTHER_ADMIN, "org_admin", OTHER_ORG, OTHER_BR)
    ensure_user(DOCTOR, "doctor", ORG, BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    _reset(ORG)
    _reset(OTHER_ORG)
    yield
    # Reference rows stay (the audit trail points at them); the policy block is
    # returned to its default so no other module inherits this one's edits.
    _reset(ORG)
    _reset(OTHER_ORG)


def _reset(org_id, *, facility_type="clinic", block=None):
    with db_session() as s:
        org = s.query(Organization).filter(Organization.id == org_id).first()
        org.facility_type = facility_type
        org.config = {"queue_calling_config": block} if block is not None else {}
        s.commit()


def _path(org_id=ORG):
    return f"/api/v1/orgs/{org_id}/queue-calling-config"


class TestEffectivePolicy:
    def test_default_is_disabled_and_says_so(self, client):
        r = client.get(_path(), headers=headers(ADMIN))
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["doctor_queue_calling_enabled"] is False
        assert body["default_doctor_queue_calling_enabled"] is False
        assert body["facility_type"] == "clinic"

    def test_a_doctor_may_read_the_policy_of_their_own_organization(self, client):
        """The queue page must know the policy before offering the Call control.

        ``org.read`` is not in the doctor role, so the read is open to the
        organization's own staff; the *write* is not (see below).
        """
        assert client.get(_path(), headers=headers(DOCTOR)).status_code == 200

    def test_a_stored_override_wins_over_the_default(self, client):
        _reset(ORG, block={"doctor_queue_calling_enabled": True})
        body = client.get(_path(), headers=headers(ADMIN)).json()
        assert body["doctor_queue_calling_enabled"] is True
        assert body["default_doctor_queue_calling_enabled"] is False

    def test_a_malformed_value_falls_back_to_the_default(self, client):
        """A corrupt block must never switch a privilege on."""
        _reset(ORG, block={"doctor_queue_calling_enabled": "yes please"})
        body = client.get(_path(), headers=headers(ADMIN)).json()
        assert body["doctor_queue_calling_enabled"] is False

    def test_doctor_only_facility_gets_the_approved_default(
            self, client, monkeypatch):
        """The approved default applies once the facility type is registered.

        No doctor-only facility type exists in the data yet (owner decision D
        requires a product decision, not an invented classifier), so the
        registered set is empty.  This test registers one value — exactly the
        change the product owner would make — and proves the default follows.
        """
        monkeypatch.setattr(config, "DOCTOR_ONLY_FACILITY_TYPES",
                            ("doctor_chamber",))
        _reset(ORG, facility_type="doctor_chamber")
        body = client.get(_path(), headers=headers(ADMIN)).json()
        assert body["doctor_queue_calling_enabled"] is True
        assert body["default_doctor_queue_calling_enabled"] is True
        assert get_queue_calling_config(
            {}, "doctor_chamber")["doctor_queue_calling_enabled"] is True

    def test_unknown_facility_type_never_enables_it(self):
        assert config.doctor_queue_calling_default("Hospital") is False
        assert config.doctor_queue_calling_default(None) is False
        assert config.doctor_queue_calling_default(7) is False


class TestWritingThePolicy:
    def test_org_admin_can_enable_it_and_the_change_is_audited(self, client):
        r = client.put(_path(), headers=headers(ADMIN),
                       json={"doctor_queue_calling_enabled": True})
        assert r.status_code == 200, r.text
        assert r.json()["doctor_queue_calling_enabled"] is True
        assert r.json()["updated_by"], "the change must say who made it"

        with db_session() as s:
            stored = s.query(Organization).filter(
                Organization.id == ORG).first().config["queue_calling_config"]
            assert stored["doctor_queue_calling_enabled"] is True
            evt = s.query(AuditEvent).filter(
                AuditEvent.action == "queue_calling_config.updated",
                AuditEvent.target_id == ORG).order_by(
                    AuditEvent.id.desc()).first()
            assert evt is not None
            assert evt.before["doctor_queue_calling_enabled"] is False
            assert evt.after["doctor_queue_calling_enabled"] is True
            assert evt.actor_id

    def test_it_can_be_turned_off_again(self, client):
        for value in (True, False):
            r = client.put(_path(), headers=headers(ADMIN),
                           json={"doctor_queue_calling_enabled": value})
            assert r.status_code == 200, r.text
            assert r.json()["doctor_queue_calling_enabled"] is value

    def test_receptionist_cannot_change_it(self, client):
        r = client.put(_path(), headers=headers(RECP),
                       json={"doctor_queue_calling_enabled": True})
        assert r.status_code == 403, r.text
        assert client.get(_path(), headers=headers(ADMIN)).json()[
            "doctor_queue_calling_enabled"] is False

    def test_a_doctor_cannot_change_it(self, client):
        """Reading the policy for the UI must not become writing it."""
        r = client.put(_path(), headers=headers(DOCTOR),
                       json={"doctor_queue_calling_enabled": True})
        assert r.status_code == 403, r.text

    def test_an_empty_body_is_a_422(self, client):
        r = client.put(_path(), headers=headers(ADMIN), json={})
        assert r.status_code == 422, r.text

    def test_a_foreign_organization_is_a_non_disclosing_404(self, client):
        for method, kwargs in (
                ("get", {}),
                ("put", {"json": {"doctor_queue_calling_enabled": True}})):
            r = getattr(client, method)(_path(OTHER_ORG), headers=headers(ADMIN),
                                        **kwargs)
            assert r.status_code == 404, (method, r.text)
        # The other organization's own administrator sees its untouched default.
        assert client.get(_path(OTHER_ORG),
                          headers=headers(OTHER_ADMIN)).json()[
            "doctor_queue_calling_enabled"] is False
