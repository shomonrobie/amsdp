"""The organization's appointment policy (owner decisions Q1 and Q5).

Two numbers decide whether a patient who arrives without a booking can be seen:
``unscheduled_daily_limit`` and ``allow_unscheduled``.  Q1 made them configuration
belonging to the organization — not a constant in the booking code — and Q5 asks
for every change to be auditable.

This module pins the administrative surface:

* the defaults, so the policy is discoverable before anyone edits it;
* a valid change, a range refusal and an empty-body refusal;
* who may read (``org.read``) and who may write (``org.manage``) — a branch
  administrator is refused, because this is an organization-wide policy;
* a foreign organization id is a non-disclosing ``404``, never a ``403``;
* the audit event carries the **before and after** policy, which is what makes a
  capacity decision reviewable after the fact.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                                ensure_user, headers, load_app, purge_org)
from common.config import (DEFAULT_UNSCHEDULED_DAILY_LIMIT,
                           MAX_UNSCHEDULED_DAILY_LIMIT)
from common.models import AuditEvent, Organization

ORG = "apptcfg-org"
OTHER_ORG = "apptcfg-other-org"
BR = "apptcfg-br"
OTHER_BR = "apptcfg-other-br"
ADMIN = "apptcfg_admin"
OTHER_ADMIN = "apptcfg_other_admin"
BRANCH_ADMIN = "apptcfg_bradm"
RECP = "apptcfg_recp"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("organization"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_user(ADMIN, "org_admin", ORG, BR)
    ensure_user(OTHER_ADMIN, "org_admin", OTHER_ORG, OTHER_BR)
    ensure_user(BRANCH_ADMIN, "branch_admin", ORG, BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    _reset_policy()
    yield
    _reset_policy()
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _reset_policy():
    """Remove the policy block so each test starts from the documented default."""
    with db_session() as s:
        org = s.query(Organization).filter(Organization.id == ORG).first()
        config = dict(org.config or {})
        config.pop("appointment_config", None)
        org.config = config
        s.commit()


def _url(org_id=ORG):
    return f"/api/v1/orgs/{org_id}/appointment-config"


def _audit(org_id=ORG):
    with db_session() as s:
        return [row for row in s.query(AuditEvent).filter(
            AuditEvent.action == "appointment_config.updated",
            AuditEvent.organization_id == org_id).order_by(
            AuditEvent.timestamp, AuditEvent.id).all()]


@pytest.fixture
def audit_before():
    """How many policy events already exist.

    The audit trail is append-only and this organization is reused across the
    module, so a test compares against a baseline instead of assuming an empty
    table — deleting trail rows to make an assertion simpler is exactly what the
    governance rules forbid.
    """
    return len(_audit())


class TestReadingThePolicy:
    def test_the_defaults_are_reported(self, client):
        response = client.get(_url(), headers=headers(ADMIN))
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["unscheduled_daily_limit"] == DEFAULT_UNSCHEDULED_DAILY_LIMIT
        assert body["allow_unscheduled"] is True
        assert body["max_unscheduled_daily_limit"] == MAX_UNSCHEDULED_DAILY_LIMIT
        assert body["updated_at"] == ""
        assert body["updated_by"] == ""

    def test_a_receptionist_may_not_read_the_policy(self, client):
        """``org.read`` is administrative; the desk does not hold it."""
        response = client.get(_url(), headers=headers(RECP))
        assert response.status_code == 403, response.text

    def test_a_foreign_organization_is_a_404(self, client):
        response = client.get(_url(OTHER_ORG), headers=headers(ADMIN))
        assert response.status_code == 404, response.text


class TestChangingThePolicy:
    def test_a_valid_change_is_applied_and_audited(self, client, audit_before):
        response = client.put(_url(), headers=headers(ADMIN),
                              json={"unscheduled_daily_limit": 3})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["unscheduled_daily_limit"] == 3
        assert body["allow_unscheduled"] is True
        assert body["updated_by"], "the policy must record who changed it"
        assert body["updated_at"]

        # The read path and the stored row agree.
        reread = client.get(_url(), headers=headers(ADMIN)).json()
        assert reread["unscheduled_daily_limit"] == 3

        events = _audit()[audit_before:]
        assert len(events) == 1
        event = events[0]
        assert event.before["unscheduled_daily_limit"] == DEFAULT_UNSCHEDULED_DAILY_LIMIT
        assert event.after["unscheduled_daily_limit"] == 3
        assert event.actor_id, "the actor is kept on the event"
        assert event.actor_role == "org_admin"

    def test_the_override_can_be_switched_off(self, client):
        response = client.put(_url(), headers=headers(ADMIN),
                              json={"allow_unscheduled": False})
        assert response.status_code == 200, response.text
        assert response.json()["allow_unscheduled"] is False
        assert _audit()[-1].after["allow_unscheduled"] is False

    def test_the_limit_is_capped_by_the_platform_maximum(self, client,
                                                         audit_before):
        too_many = client.put(_url(), headers=headers(ADMIN),
                              json={"unscheduled_daily_limit":
                                    MAX_UNSCHEDULED_DAILY_LIMIT + 1})
        assert too_many.status_code == 422, too_many.text
        assert "between 1 and" in too_many.json()["detail"]
        assert client.put(_url(), headers=headers(ADMIN),
                          json={"unscheduled_daily_limit": 0}
                          ).status_code == 422
        assert len(_audit()) == audit_before, (
            "a refused change must not be audited as a change")

    def test_an_empty_update_is_refused(self, client, audit_before):
        response = client.put(_url(), headers=headers(ADMIN), json={})
        assert response.status_code == 422, response.text
        assert len(_audit()) == audit_before

    def test_a_branch_admin_cannot_change_the_policy(self, client, audit_before):
        response = client.put(_url(), headers=headers(BRANCH_ADMIN),
                              json={"unscheduled_daily_limit": 2})
        assert response.status_code == 403, response.text
        assert len(_audit()) == audit_before

    def test_a_foreign_organizations_admin_cannot_change_it(self, client,
                                                             audit_before):
        response = client.put(_url(), headers=headers(OTHER_ADMIN),
                              json={"unscheduled_daily_limit": 2})
        assert response.status_code == 404, response.text
        assert len(_audit()) == audit_before

    def test_two_changes_are_two_audit_events(self, client, audit_before):
        """The trail is a sequence, not a single overwritten record."""
        assert client.put(_url(), headers=headers(ADMIN),
                          json={"unscheduled_daily_limit": 2}).status_code == 200
        assert client.put(_url(), headers=headers(ADMIN),
                          json={"unscheduled_daily_limit": 4}).status_code == 200
        events = _audit()[audit_before:]
        assert len(events) == 2
        assert [e.after["unscheduled_daily_limit"] for e in events] == [2, 4]
        assert events[0].before["unscheduled_daily_limit"] == DEFAULT_UNSCHEDULED_DAILY_LIMIT
        assert events[1].before["unscheduled_daily_limit"] == 2
