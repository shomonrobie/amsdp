"""MP-17 — doctor mobile-number duplicate allowance, end to end (BR §9.6–§9.8).

The three rules this module exercises:

    §9.6  default: one doctor per mobile number **within** an organization;
    §9.7  a Super Admin may allow duplicates **within** that organization;
    §9.8  the same number may always exist in a *different* organization.

§9.8 is the one that must hold whatever the switch says: the duplicate lookup is
scoped by ``organization_id``, so turning the allowance on at one facility can
never let it collide with — or be blocked by — another tenant's doctors.

The policy itself is read by ``common.config`` (see
``tests/test_doctor_mobile_policy.py``, which needs no database).  What is tested
here is the *enforcement*: ``create_doctor`` and ``update_doctor`` both consult
the same helper, so a repeat number is a 409 unless the tenant has been granted
the allowance, on both paths.

Reference rows are never deleted by the suite (the audit trail points at them),
so every doctor here gets a fresh mobile number, and the organization's policy is
reset before and after each test — the organization row itself survives
``purge_org``.
"""

import itertools
import uuid

import pytest
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_org,
                               ensure_user, headers, load_app, purge_org)
from common.models import AuditEvent, Doctor, Organization

ORG = "mp17-doc-org"
BR = "mp17-doc-br"
OTHER_ORG = "mp17-doc-other-org"
OTHER_BR = "mp17-doc-other-br"

#: Manages doctors in ORG (holds ``doctor.*``), but is **not** a platform
#: administrator — so it must not be able to grant the allowance.
ADMIN = "mp17_doc_admin"
#: Holds ``org.manage`` without being a platform administrator: the caller for
#: which the platform gate is the binding one (D-2).
ORGADMIN = "mp17_doc_org_admin"
#: Platform administrator: holds ``platform.admin``, which is what
#: ``AuthContext.is_super_admin`` asks for (Q-1).
PLATFORM = "mp17_doc_platform"
#: The same job at the other tenant — the §9.8 witness.
OTHER_ADMIN = "mp17_doc_other_admin"

POLICY = "/api/v1/orgs/{org}/doctor-mobile-policy"


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("doctor"))


def _set_policy(org_id: str, allow: bool) -> None:
    """Write the allowance straight to the row: test setup, not the thing tested."""
    with db_session() as s:
        org = s.query(Organization).filter(Organization.id == org_id).first()
        if org is None:
            return
        config = dict(org.config or {})
        config["doctor_mobile_policy"] = {"allow_duplicate_mobile": allow}
        org.config = config
        s.commit()


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_user(ADMIN, "branch_admin", ORG, BR)
    ensure_user(ORGADMIN, "org_admin", ORG, None)
    ensure_user(PLATFORM, "super_admin", ORG, None)
    ensure_user(OTHER_ADMIN, "branch_admin", OTHER_ORG, OTHER_BR)
    # The organization row survives purge_org, so the policy does too.
    _set_policy(ORG, False)
    yield
    _set_policy(ORG, False)
    purge_org(ORG)
    purge_org(OTHER_ORG)


_MOBILE_BASE = int(uuid.uuid4().int % 900000) * 1000
_MOBILE_SEQ = itertools.count(1)


def _next_mobile() -> str:
    """A canonical BD mobile number unique to this process run."""
    return f"018{(_MOBILE_BASE + next(_MOBILE_SEQ)) % 100000000:08d}"


def _create(client, user: str, mobile: str, name: str = "Dr. Duplicate"):
    return client.post("/api/v1/doctors", headers=headers(user),
                       json={"name": name, "mobile": mobile})


def _doctors_on(org_id: str, mobile: str) -> int:
    with db_session() as s:
        return s.query(Doctor).filter(Doctor.organization_id == org_id,
                                      Doctor.mobile == mobile).count()


# ---------------------------------------------------------------------------
# BR §9.6 — unique by default
# ---------------------------------------------------------------------------

def test_default_refuses_a_second_doctor_on_the_same_mobile(client):
    mobile = _next_mobile()
    assert _create(client, ADMIN, mobile).status_code == 201
    second = _create(client, ADMIN, mobile, name="Dr. Same Number")
    assert second.status_code == 409
    assert _doctors_on(ORG, mobile) == 1


def test_the_check_uses_the_canonical_form(client):
    """``+880 18…`` and ``018…`` are one number, so the second is a 409 too."""
    mobile = _next_mobile()
    assert _create(client, ADMIN, mobile).status_code == 201
    international = "+880 " + mobile[1:]
    assert _create(client, ADMIN, international).status_code == 409


# ---------------------------------------------------------------------------
# BR §9.7 — a platform administrator may allow it, nobody else
# ---------------------------------------------------------------------------

def test_only_a_platform_administrator_may_grant_the_allowance(client):
    # D-2: two gates stand in front of this switch and they answer differently on
    # purpose. A caller who cannot manage the organization is refused at the
    # capability gate and told nothing about a platform-level setting; a caller
    # who *can* manage it — but is not a platform administrator — is refused by
    # BR §9.7 and told exactly that.
    denied = client.patch(POLICY.format(org=ORG), headers=headers(ADMIN),
                          json={"allow_duplicate_mobile": True})
    assert denied.status_code == 403
    assert "platform administrator" not in denied.text

    org_denied = client.patch(POLICY.format(org=ORG), headers=headers(ORGADMIN),
                              json={"allow_duplicate_mobile": True})
    assert org_denied.status_code == 403
    assert "platform administrator" in org_denied.text

    # Neither attempt wrote anything: the default still refuses the duplicate.
    mobile = _next_mobile()
    assert _create(client, ADMIN, mobile).status_code == 201
    assert _create(client, ADMIN, mobile).status_code == 409


def test_the_allowance_can_be_read_by_doctor_management(client):
    read = client.get(POLICY.format(org=ORG), headers=headers(ADMIN))
    assert read.status_code == 200
    assert read.json() == {"organization_id": ORG,
                           "doctor_mobile_policy":
                               {"allow_duplicate_mobile": False}}


def test_the_allowance_permits_duplicates_within_the_organization(client):
    granted = client.patch(POLICY.format(org=ORG), headers=headers(PLATFORM),
                           json={"allow_duplicate_mobile": True})
    assert granted.status_code == 200
    assert granted.json()["doctor_mobile_policy"] == {
        "allow_duplicate_mobile": True}

    mobile = _next_mobile()
    assert _create(client, ADMIN, mobile).status_code == 201
    assert _create(client, ADMIN, mobile, name="Dr. Locum").status_code == 201
    assert _doctors_on(ORG, mobile) == 2


def test_withdrawing_the_allowance_keeps_duplicates_but_refuses_a_third(client):
    client.patch(POLICY.format(org=ORG), headers=headers(PLATFORM),
                 json={"allow_duplicate_mobile": True})
    mobile = _next_mobile()
    assert _create(client, ADMIN, mobile).status_code == 201
    assert _create(client, ADMIN, mobile).status_code == 201

    withdrawn = client.patch(POLICY.format(org=ORG), headers=headers(PLATFORM),
                             json={"allow_duplicate_mobile": False})
    assert withdrawn.status_code == 200
    # Prospective only: the two rows that already share the number stay.
    assert _doctors_on(ORG, mobile) == 2
    assert _create(client, ADMIN, mobile, name="Dr. Third").status_code == 409


def test_the_policy_change_is_audited_with_before_and_after(client):
    client.patch(POLICY.format(org=ORG), headers=headers(PLATFORM),
                 json={"allow_duplicate_mobile": True})
    with db_session() as s:
        row = s.query(AuditEvent).filter(
            AuditEvent.organization_id == ORG,
            AuditEvent.action == "organization.doctor_mobile_policy.update",
        ).order_by(AuditEvent.timestamp.desc()).first()
        assert row is not None
        assert row.target_type == "organization"
        assert row.before == {"allow_duplicate_mobile": False}
        assert row.after == {"allow_duplicate_mobile": True}
        assert row.actor_id


# ---------------------------------------------------------------------------
# BR §9.8 — the allowance never crosses a tenant boundary
# ---------------------------------------------------------------------------

def test_a_number_used_at_another_facility_is_never_a_duplicate(client):
    mobile = _next_mobile()
    assert _create(client, ADMIN, mobile).status_code == 201
    # The other tenant is on the default policy: still allowed, because tenancy —
    # not the allowance — is what separates the two facilities.
    assert _create(client, OTHER_ADMIN, mobile,
                   name="Dr. Other Facility").status_code == 201
    assert _doctors_on(ORG, mobile) == 1
    assert _doctors_on(OTHER_ORG, mobile) == 1


def test_the_allowance_at_one_facility_does_not_reach_another(client):
    client.patch(POLICY.format(org=ORG), headers=headers(PLATFORM),
                 json={"allow_duplicate_mobile": True})
    mobile = _next_mobile()
    assert _create(client, ADMIN, mobile).status_code == 201
    assert _create(client, ADMIN, mobile).status_code == 201
    # The duplicate check never looked outside its own tenant, which is what
    # §9.8 requires whichever way the allowance is set.
    assert _doctors_on(OTHER_ORG, mobile) == 0


# ---------------------------------------------------------------------------
# The update path obeys the same rule
# ---------------------------------------------------------------------------

def _two_doctors(client):
    first, second = _next_mobile(), _next_mobile()
    a = _create(client, ADMIN, first, name="Dr. First").json()
    b = _create(client, ADMIN, second, name="Dr. Second").json()
    return a, b, first, second


def test_update_refuses_a_number_another_doctor_already_has(client):
    a, b, first, second = _two_doctors(client)
    moved = client.patch(f"/api/v1/doctors/{b['id']}", headers=headers(ADMIN),
                         json={"mobile": first})
    assert moved.status_code == 409
    assert _doctors_on(ORG, first) == 1


def test_update_accepts_a_collision_when_the_org_allows_it(client):
    a, b, first, second = _two_doctors(client)
    client.patch(POLICY.format(org=ORG), headers=headers(PLATFORM),
                 json={"allow_duplicate_mobile": True})
    moved = client.patch(f"/api/v1/doctors/{b['id']}", headers=headers(ADMIN),
                         json={"mobile": first})
    assert moved.status_code == 200
    assert moved.json()["mobile"] == first
    assert _doctors_on(ORG, first) == 2


def test_resaving_a_doctor_does_not_collide_with_itself(client):
    """The update check excludes the doctor being edited."""
    a, b, first, second = _two_doctors(client)
    same = client.patch(f"/api/v1/doctors/{a['id']}", headers=headers(ADMIN),
                        json={"mobile": first, "name": "Dr. Renamed"})
    assert same.status_code == 200
    assert same.json()["name"] == "Dr. Renamed"
