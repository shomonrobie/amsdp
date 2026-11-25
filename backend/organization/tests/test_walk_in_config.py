"""Organization walk-in placement policy (MP-10 / BR §24–§25).

Covers the *organization* half: the effective value and its defaults, who may
read and who may write, the platform-defined set of options, the reserve bounds,
tenant scoping, the prospective-only guarantee and the audit record. The
behaviour of each policy in the queue is proven in
``backend/queuing/tests/test_walk_in_placement.py``.
"""

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                               ensure_user, headers, load_app)
from common.config import WALK_IN_POLICIES
from common.models import AuditEvent, Organization

ORG = "wic-org"
BR = "wic-branch"
OTHER_ORG = "wic-other-org"
OTHER_BR = "wic-other-branch"
ADMIN = "wic_admin"
DOCTOR = "wic_doctor"
RECP = "wic_recp"
SUPER = "wic_super"


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
    ensure_user(DOCTOR, "doctor", ORG, BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(SUPER, "super_admin", ORG, None)
    _reset(ORG)
    _reset(OTHER_ORG)
    yield
    # The policy block is returned to its default so no other module inherits
    # this one's edits; reference rows stay (the audit trail points at them).
    _reset(ORG)
    _reset(OTHER_ORG)


def _reset(org_id, block=None):
    with db_session() as s:
        org = s.query(Organization).filter(Organization.id == org_id).first()
        org.config = {"queue_config": block} if block is not None else {}
        s.commit()


def _path(org_id=ORG):
    return f"/api/v1/orgs/{org_id}/walk-in-config"


class TestEffectivePolicy:
    def test_the_default_is_end_of_queue_with_no_reserve(self, client):
        body = client.get(_path(), headers=headers(ADMIN)).json()
        assert body["walk_in_policy"] == "end_of_queue"
        assert body["walk_in_reserve_mode"] == "percent"
        assert body["walk_in_reserve_value"] == 0
        assert body["updated_at"] == "" and body["updated_by"] == ""

    def test_the_platform_set_is_offered_and_the_bounds_are_published(self, client):
        body = client.get(_path(), headers=headers(ADMIN)).json()
        assert body["allowed_walk_in_policies"] == list(WALK_IN_POLICIES)
        assert body["limits"] == {"percent": 100, "count": 100}

    def test_front_desk_and_doctor_can_read_it(self, client):
        """The walk-in form needs it before it can render a position field."""
        assert client.get(_path(), headers=headers(RECP)).status_code == 200
        assert client.get(_path(), headers=headers(DOCTOR)).status_code == 200

    def test_a_stored_policy_is_returned(self, client):
        _reset(ORG, {"walk_in_policy": "first_come",
                     "walk_in_reserve_mode": "count",
                     "walk_in_reserve_value": 3})
        body = client.get(_path(), headers=headers(ADMIN)).json()
        assert body["walk_in_policy"] == "first_come"
        assert body["walk_in_reserve_mode"] == "count"
        assert body["walk_in_reserve_value"] == 3

    def test_a_malformed_policy_falls_back_without_refusing(self, client):
        _reset(ORG, {"walk_in_policy": "round_robin",
                     "walk_in_reserve_value": "not a number"})
        body = client.get(_path(), headers=headers(ADMIN)).json()
        assert body["walk_in_policy"] == "end_of_queue"
        assert body["walk_in_reserve_value"] == 0

    def test_a_foreign_organization_is_a_non_disclosing_404(self, client):
        r = client.get(_path(OTHER_ORG), headers=headers(ADMIN))
        assert r.status_code == 404, r.text


class TestWritingThePolicy:
    def test_the_facility_administrator_selects_a_policy_and_it_is_audited(
            self, client):
        r = client.put(_path(), headers=headers(ADMIN),
                       json={"walk_in_policy": "reserved_capacity"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["walk_in_policy"] == "reserved_capacity"
        assert body["updated_by"], "the change must say who made it"

        with db_session() as s:
            org = s.query(Organization).filter(Organization.id == ORG).first()
            assert org.config["queue_config"]["walk_in_policy"] == \
                "reserved_capacity"
            # ``AuditEvent.id`` is a random UUID, so "the newest row" is not
            # ``order_by(id.desc())``. The trail is append-only across runs, so
            # the test asserts the *transition it caused* exists rather than
            # guessing which row came last.
            rows = s.query(AuditEvent).filter(
                AuditEvent.action == "walk_in_config.updated",
                AuditEvent.target_id == ORG).all()
            matches = [
                row for row in rows
                if isinstance(row.before, dict) and isinstance(row.after, dict)
                and row.before.get("walk_in_policy") == "end_of_queue"
                and row.after.get("walk_in_policy") == "reserved_capacity"
                and row.actor_id
            ]
            assert matches, "the change must be audited with before and after"

    def test_the_reserve_can_be_set_in_either_mode(self, client):
        r = client.put(_path(), headers=headers(ADMIN),
                       json={"walk_in_reserve_mode": "count",
                             "walk_in_reserve_value": 4})
        assert r.status_code == 200, r.text
        assert r.json()["walk_in_reserve_mode"] == "count"
        assert r.json()["walk_in_reserve_value"] == 4

    def test_a_partial_update_leaves_the_other_fields_alone(self, client):
        _reset(ORG, {"walk_in_policy": "first_come",
                     "walk_in_reserve_mode": "count",
                     "walk_in_reserve_value": 2})
        r = client.put(_path(), headers=headers(ADMIN),
                       json={"walk_in_reserve_value": 5})
        assert r.status_code == 200, r.text
        assert r.json()["walk_in_policy"] == "first_come"
        assert r.json()["walk_in_reserve_mode"] == "count"
        assert r.json()["walk_in_reserve_value"] == 5

    def test_an_unrelated_config_block_survives_the_write(self, client):
        with db_session() as s:
            org = s.query(Organization).filter(Organization.id == ORG).first()
            org.config = {"queue_calling_config": {
                "doctor_queue_calling_enabled": True}}
            s.commit()
        assert client.put(_path(), headers=headers(ADMIN),
                          json={"walk_in_policy": "first_come"}).status_code == 200
        with db_session() as s:
            org = s.query(Organization).filter(Organization.id == ORG).first()
            assert org.config["queue_calling_config"][
                "doctor_queue_calling_enabled"] is True

    def test_it_can_be_set_back_to_the_default(self, client):
        assert client.put(_path(), headers=headers(ADMIN),
                          json={"walk_in_policy": "staff_placement"}
                          ).status_code == 200
        r = client.put(_path(), headers=headers(ADMIN),
                       json={"walk_in_policy": "end_of_queue"})
        assert r.status_code == 200 and r.json()["walk_in_policy"] == "end_of_queue"


class TestRefusals:
    def test_front_desk_cannot_change_it(self, client):
        r = client.put(_path(), headers=headers(RECP),
                       json={"walk_in_policy": "staff_placement"})
        assert r.status_code == 403, r.text
        assert client.get(_path(), headers=headers(ADMIN)).json()[
            "walk_in_policy"] == "end_of_queue"

    def test_a_doctor_cannot_change_it(self, client):
        """Reading the policy for the form must not become writing it."""
        assert client.put(_path(), headers=headers(DOCTOR),
                          json={"walk_in_policy": "first_come"}).status_code == 403

    def test_a_foreign_administrator_gets_a_non_disclosing_404(self, client):
        other = ensure_user("wic_other_admin", "org_admin", OTHER_ORG, OTHER_BR)
        r = client.put(_path(ORG), headers=headers("wic_other_admin"),
                       json={"walk_in_policy": "first_come"})
        assert r.status_code == 404, (other, r.text)

    def test_an_unknown_policy_is_refused(self, client):
        r = client.put(_path(), headers=headers(ADMIN),
                       json={"walk_in_policy": "round_robin"})
        assert r.status_code == 422, r.text

    def test_an_empty_body_is_refused(self, client):
        assert client.put(_path(), headers=headers(ADMIN), json={}
                          ).status_code == 422

    def test_the_reserve_bounds_are_enforced(self, client):
        for body in ({"walk_in_reserve_value": 101},
                     {"walk_in_reserve_value": -1},
                     {"walk_in_reserve_mode": "bananas"},
                     {"walk_in_reserve_mode": "count",
                      "walk_in_reserve_value": 101}):
            r = client.put(_path(), headers=headers(ADMIN), json=body)
            assert r.status_code == 422, (body, r.text)

    def test_a_refused_write_changes_nothing(self, client):
        client.put(_path(), headers=headers(ADMIN),
                   json={"walk_in_policy": "first_come"})
        assert client.put(_path(), headers=headers(ADMIN),
                          json={"walk_in_reserve_value": 999}).status_code == 422
        body = client.get(_path(), headers=headers(ADMIN)).json()
        assert body["walk_in_policy"] == "first_come"
        assert body["walk_in_reserve_value"] == 0


class TestPlatformSet:
    """BR §25 — "Super Admin defines available options/limits"."""

    def test_only_a_platform_administrator_may_narrow_the_options(self, client):
        r = client.put(_path(), headers=headers(ADMIN),
                       json={"allowed_walk_in_policies": ["end_of_queue"]})
        assert r.status_code == 403, r.text

    def test_a_platform_administrator_narrows_the_set(self, client):
        r = client.put(_path(), headers=headers(SUPER),
                       json={"allowed_walk_in_policies": ["end_of_queue",
                                                          "first_come"]})
        assert r.status_code == 200, r.text
        assert r.json()["allowed_walk_in_policies"] == ["end_of_queue",
                                                       "first_come"]

    def test_the_facility_may_not_select_an_option_outside_the_set(self, client):
        client.put(_path(), headers=headers(SUPER),
                   json={"allowed_walk_in_policies": ["end_of_queue",
                                                      "first_come"]})
        r = client.put(_path(), headers=headers(ADMIN),
                       json={"walk_in_policy": "staff_placement"})
        assert r.status_code == 422, r.text
        assert "not available" in r.json()["detail"]
        assert client.put(_path(), headers=headers(ADMIN),
                          json={"walk_in_policy": "first_come"}).status_code == 200

    def test_narrowing_below_the_current_policy_falls_back_safely(self, client):
        """Withdrawing the chosen option must not leave an unusable policy."""
        client.put(_path(), headers=headers(ADMIN),
                   json={"walk_in_policy": "reserved_capacity"})
        r = client.put(_path(), headers=headers(SUPER),
                       json={"allowed_walk_in_policies": ["end_of_queue"]})
        assert r.status_code == 200, r.text
        assert r.json()["walk_in_policy"] == "end_of_queue", \
            "the effective policy falls back to the least surprising one"

    def test_an_empty_or_unknown_option_set_is_refused(self, client):
        for body in ({"allowed_walk_in_policies": []},
                     {"allowed_walk_in_policies": ["round_robin"]}):
            r = client.put(_path(), headers=headers(SUPER), json=body)
            assert r.status_code == 422, (body, r.text)
