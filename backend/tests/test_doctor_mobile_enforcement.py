"""MP-17 — the duplicate check's *decision*, without a database.

``assert_mobile_available`` is the one place both doctor write paths ask "may
this number be used here?".  It takes a session and an optional organization row,
so its decision can be pinned with a recording stub:

* the platform default refuses a collision (BR §9.6);
* the allowance skips the lookup entirely — an allowed duplicate must not even
  cost a query, and must never be refused (BR §9.7);
* a missing organization row is strict, not permissive;
* the edit path excludes the doctor being edited, so re-saving a doctor whose
  number is unchanged cannot collide with itself.

The API-level proof — 409/201 from real endpoints, cross-tenant separation and the
audit row — is ``doctor/tests/test_doctor_mobile_duplicates.py``, which needs
PostgreSQL and therefore does not run on a host without it.
"""

import pytest
from fastapi import HTTPException

from doctor.profile import assert_mobile_available


class _Org:
    """The only attribute the helper reads from an organization row."""

    def __init__(self, config):
        self.config = config


class _RecordingSession:
    """Counts queries and filters, and answers ``first()`` with *hit*."""

    def __init__(self, hit=None):
        self.hit = hit
        self.queries = 0
        self.filters = 0

    def query(self, model):
        session = self

        class _Query:
            def filter(self, *criteria):
                session.filters += 1
                return self

            def first(self):
                return session.hit

        session.queries += 1
        return _Query()


def test_the_default_refuses_a_collision():
    session = _RecordingSession(hit=object())
    with pytest.raises(HTTPException) as raised:
        assert_mobile_available(session, _Org({}), "org-1", "01800000001")
    assert raised.value.status_code == 409
    assert "already exists" in str(raised.value.detail)


def test_the_allowance_skips_the_lookup_and_allows_the_duplicate():
    session = _RecordingSession(hit=object())
    org = _Org({"doctor_mobile_policy": {"allow_duplicate_mobile": True}})
    assert assert_mobile_available(session, org, "org-1", "01800000001") is None
    assert session.queries == 0, "an allowed duplicate must not cost a query"


def test_a_free_number_is_allowed_under_the_default():
    session = _RecordingSession(hit=None)
    assert assert_mobile_available(session, _Org({}), "org-1",
                                   "01800000001") is None
    assert (session.queries, session.filters) == (1, 1)


def test_the_edit_path_excludes_the_doctor_being_edited():
    session = _RecordingSession(hit=None)
    assert_mobile_available(session, _Org({}), "org-1", "01800000001",
                            exclude_doctor_id="doc-1")
    assert session.filters == 2, "org, mobile and the excluded doctor"


def test_a_missing_organization_row_is_strict_not_permissive():
    """A caller with no config to read gets the default, never an allowance."""
    session = _RecordingSession(hit=object())
    with pytest.raises(HTTPException) as raised:
        assert_mobile_available(session, None, "org-1", "01800000001")
    assert raised.value.status_code == 409


def test_a_corrupt_policy_block_is_strict_not_permissive():
    session = _RecordingSession(hit=object())
    org = _Org({"doctor_mobile_policy": "allow everything"})
    with pytest.raises(HTTPException) as raised:
        assert_mobile_available(session, org, "org-1", "01800000001")
    assert raised.value.status_code == 409
