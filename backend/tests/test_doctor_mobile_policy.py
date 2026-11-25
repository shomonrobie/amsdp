"""MP-17 — the doctor mobile-number duplicate policy, without a database.

BR §9.6–§9.8 make three statements with one switch in the middle:

    §9.6  default doctor mobile-number uniqueness is within an organization;
    §9.7  Super Admin may allow duplicate doctor mobile numbers within an
          organization;
    §9.8  the same mobile number may exist in different organizations.

The switch is a *platform* default of "unique" that a platform administrator can
lift per organization (``common.config.doctor_mobile_policy``).  §9.8 is not part
of the switch: tenancy settles it, and the service's duplicate lookup is scoped
by ``organization_id`` — see ``doctor/tests/test_doctor_mobile_duplicates.py`` for
the API-level proof, which needs PostgreSQL.

This module is deliberately DB-free.  It pins the *reading* of the setting — the
half that decides whether the API refuses a repeat number — so a malformed or
absent configuration block can never be mistaken for permission.  It imports
only ``common.config`` (constants and pure functions), so it runs on a host with
no database at all.
"""

import pytest

from common.config import (DEFAULT_DOCTOR_MOBILE_POLICY,
                           doctor_mobile_must_be_unique,
                           get_doctor_mobile_policy,
                           merge_doctor_mobile_policy)


# ---------------------------------------------------------------------------
# Defaults: missing or unusable configuration means "unique"
# ---------------------------------------------------------------------------

def test_the_platform_default_is_unique_within_the_organization():
    """BR §9.6: with nothing configured, two doctors cannot share a number."""
    assert DEFAULT_DOCTOR_MOBILE_POLICY == {"allow_duplicate_mobile": False}
    assert get_doctor_mobile_policy(None)["allow_duplicate_mobile"] is False
    assert doctor_mobile_must_be_unique(None) is True


def test_an_organization_with_no_policy_block_is_unique():
    assert get_doctor_mobile_policy({}) == {"allow_duplicate_mobile": False}
    assert get_doctor_mobile_policy({"registration_policy": {}}) == {
        "allow_duplicate_mobile": False}


def test_an_empty_policy_block_is_unique():
    assert doctor_mobile_must_be_unique({"doctor_mobile_policy": {}}) is True


@pytest.mark.parametrize("stored", [
    "yes", "false", "true", 1, 0, None, [], {}, ["allow_duplicate_mobile"],
])
def test_a_non_boolean_value_is_ignored_not_coerced(stored):
    """A corrupt block must never switch a uniqueness rule off."""
    config = {"doctor_mobile_policy": {"allow_duplicate_mobile": stored}}
    assert get_doctor_mobile_policy(config)["allow_duplicate_mobile"] is False
    assert doctor_mobile_must_be_unique(config) is True


@pytest.mark.parametrize("block", ["allow_duplicate_mobile", 42, []])
def test_a_malformed_policy_block_is_ignored(block):
    assert doctor_mobile_must_be_unique({"doctor_mobile_policy": block}) is True


# ---------------------------------------------------------------------------
# The allowance: an explicit platform decision, stored per organization
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("allow", [True, False])
def test_an_explicit_boolean_decides_the_switch(allow):
    config = {"doctor_mobile_policy": {"allow_duplicate_mobile": allow}}
    assert get_doctor_mobile_policy(config)["allow_duplicate_mobile"] is allow
    assert doctor_mobile_must_be_unique(config) is (not allow)


def test_enforcing_uniqueness_is_the_negation_of_the_stored_allowance():
    """The API asks one question; it must not be able to disagree with itself."""
    for allow in (True, False):
        config = {"doctor_mobile_policy": {"allow_duplicate_mobile": allow}}
        assert (doctor_mobile_must_be_unique(config)
                is not get_doctor_mobile_policy(config)[
                    "allow_duplicate_mobile"])


def test_reading_the_policy_returns_a_copy_not_the_shared_default():
    """A caller mutating the returned dict must not edit the platform default."""
    policy = get_doctor_mobile_policy(None)
    policy["allow_duplicate_mobile"] = True
    assert DEFAULT_DOCTOR_MOBILE_POLICY["allow_duplicate_mobile"] is False
    assert doctor_mobile_must_be_unique(None) is True


# ---------------------------------------------------------------------------
# Writing the policy block
# ---------------------------------------------------------------------------

def test_merge_sets_the_block_and_leaves_other_configuration_alone():
    config = {"registration_policy": {"bmdc_required": True},
              "queue_config": {"walk_in_policy": "first_come"}}
    merged = merge_doctor_mobile_policy(
        config, {"allow_duplicate_mobile": True})
    assert merged["doctor_mobile_policy"]["allow_duplicate_mobile"] is True
    assert merged["registration_policy"] == {"bmdc_required": True}
    assert merged["queue_config"] == {"walk_in_policy": "first_come"}
    # The caller's dict is not mutated: the request either commits or rolls back.
    assert "doctor_mobile_policy" not in config


def test_merge_ignores_none_values():
    config = {"doctor_mobile_policy": {"allow_duplicate_mobile": True}}
    merged = merge_doctor_mobile_policy(config,
                                        {"allow_duplicate_mobile": None})
    assert merged["doctor_mobile_policy"]["allow_duplicate_mobile"] is True


def test_merge_can_withdraw_the_allowance():
    config = {"doctor_mobile_policy": {"allow_duplicate_mobile": True}}
    merged = merge_doctor_mobile_policy(
        config, {"allow_duplicate_mobile": False})
    assert merged["doctor_mobile_policy"]["allow_duplicate_mobile"] is False
    assert doctor_mobile_must_be_unique(merged) is True


def test_merge_from_nothing_is_a_valid_configuration():
    merged = merge_doctor_mobile_policy(None, {"allow_duplicate_mobile": True})
    assert merged == {"doctor_mobile_policy": {"allow_duplicate_mobile": True}}
    assert doctor_mobile_must_be_unique(merged) is False
