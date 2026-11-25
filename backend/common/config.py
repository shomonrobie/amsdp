"""AMSDP org/branch queue configuration helpers (default-disabled).

Reads ``queue_config`` from the Organization ``config`` JSON:

    {
      "queue_config": {
        "walk_in_policy": "end_of_queue" | "first_come"
                          | "reserved_capacity" | "staff_placement",
        "walk_in_reserve_mode": "percent" | "count",
        "walk_in_reserve_value": int,   # percent of capacity, or fixed count
        "allowed_walk_in_policies": ["end_of_queue", ...]   # platform set
      }
    }

Default: no reservation configured, placement ``end_of_queue`` — behaviour
identical to prior releases.
"""

#: Walk-in placement policies (Business Rules §25).  The platform set: BR §25
#: says a *Super Admin defines the available options* and the *Facility Admin
#: selects* one, so this tuple is the superset a facility may be allowed to
#: choose from, and ``allowed_walk_in_policies`` narrows it per organization.
WALK_IN_POLICIES = ("end_of_queue", "first_come", "reserved_capacity",
                    "staff_placement")

#: The behaviour that reorders the least, and therefore the fallback for a
#: missing, unknown or no-longer-allowed policy.
DEFAULT_WALK_IN_POLICY = "end_of_queue"

#: Upper bounds for the reserve configuration.  100 % reserves the whole day;
#: the booking path already refuses to reserve more than the slot holds.
MAX_WALK_IN_RESERVE_PERCENT = 100
MAX_WALK_IN_RESERVE_COUNT = 100


def allowed_walk_in_policies(org_config=None) -> list:
    """The placement policies this organization may select.

    A platform administrator can narrow the set through
    ``queue_config.allowed_walk_in_policies``; everyone else inherits the
    platform set.  An empty or malformed value means *the platform set* — a
    corrupt block must not leave a facility with no usable policy at all.
    """
    raw = ((org_config or {}).get("queue_config") or {}).get(
        "allowed_walk_in_policies")
    if not isinstance(raw, (list, tuple)):
        return list(WALK_IN_POLICIES)
    allowed = [p for p in WALK_IN_POLICIES if p in raw]
    return allowed or list(WALK_IN_POLICIES)


def get_queue_config(org_config=None) -> dict:
    """The organisation's queue configuration block, with safe fallbacks.

    Two things are read from ``queue_config``: the walk-in **reserve split**
    (how much published capacity is held back from advance bookings) and the
    walk-in **placement policy** (where a walk-in joins the queue).  Both live
    in one block so a facility has one queue policy to read and one to audit.

    Every malformed value falls back rather than raising: a corrupt
    configuration block must never make enqueueing or booking answer a 500, and
    it must never widen a privilege.  A policy that is not in the allowed set
    falls back to :data:`DEFAULT_WALK_IN_POLICY`, which is the behaviour that
    reorders the least.
    """
    cfg = (org_config or {}).get("queue_config") or {}
    mode = cfg.get("walk_in_reserve_mode")
    if mode not in ("percent", "count"):
        mode = "percent"
    try:
        value = int(cfg.get("walk_in_reserve_value") or 0)
    except (TypeError, ValueError):
        value = 0
    allowed = allowed_walk_in_policies(org_config)
    policy = cfg.get("walk_in_policy")
    if not isinstance(policy, str) or policy not in allowed:
        policy = (DEFAULT_WALK_IN_POLICY if DEFAULT_WALK_IN_POLICY in allowed
                  else allowed[0])
    return {"walk_in_reserve_mode": mode,
            "walk_in_reserve_value": max(value, 0),
            "walk_in_policy": policy,
            "allowed_walk_in_policies": allowed}


def reserved_for_capacity(capacity: int, org_config=None) -> int:
    """Number of slots reserved for walk-ins for a capacity of *capacity*."""
    cfg = get_queue_config(org_config)
    value = cfg["walk_in_reserve_value"]
    if value <= 0 or capacity <= 0:
        return 0
    if cfg["walk_in_reserve_mode"] == "count":
        return min(value, capacity)
    return int(round(capacity * value / 100.0))


def get_walk_in_config(org_config=None) -> dict:
    """The effective walk-in policy for one organization, plus its provenance.

    The effective values come from :func:`get_queue_config` so the queuing
    service, the booking path and this view can never disagree.  ``updated_at``
    and ``updated_by`` are whatever the last administrative write recorded; they
    are returned as strings so a malformed value cannot break a response.
    """
    cfg = get_queue_config(org_config)
    stored = (org_config or {}).get("queue_config") or {}
    cfg["updated_at"] = str(stored.get("updated_at") or "")
    cfg["updated_by"] = str(stored.get("updated_by") or "")
    return cfg


def merge_walk_in_config(org_config, updates: dict) -> dict:
    """Return a copy of *org_config* with the walk-in policy fields applied.

    ``None`` means "leave unchanged", exactly like
    :func:`merge_appointment_config`, so a partial update never erases a value
    the caller did not name.
    """
    merged = dict(org_config or {})
    block = dict(merged.get("queue_config") or {})
    block.update({k: v for k, v in (updates or {}).items() if v is not None})
    merged["queue_config"] = block
    return merged


#: Staff override policy (AMSDP-APPT-OWNER-DECISIONS-01, owner decision Q1).
#:
#: An outside-session ("unscheduled") appointment is limited per doctor per day,
#: so the override cannot become an unlimited dumping ground.  Five is the
#: default for a chamber that normally sees scheduled patients and takes a few
#: walk-ins; an organization that needs more sets it explicitly through
#: ``PUT /api/v1/orgs/{id}/appointment-config`` (audited, Q5).
#:
#: ``allow_unscheduled`` is the organization's switch: when an organization turns
#: the override off, outside-session bookings are refused outright rather than
#: silently accepted under the limit.
DEFAULT_UNSCHEDULED_DAILY_LIMIT = 5
MAX_UNSCHEDULED_DAILY_LIMIT = 100


def get_appointment_config(org_config=None) -> dict:
    """Read ``appointment_config`` from the Organization ``config`` JSON.

    Unknown or malformed values fall back to the defaults rather than raising: a
    corrupt configuration block must never make booking answer a 500.
    """
    cfg = (org_config or {}).get("appointment_config") or {}
    try:
        limit = int(cfg.get("unscheduled_daily_limit",
                            DEFAULT_UNSCHEDULED_DAILY_LIMIT))
    except (TypeError, ValueError):
        limit = DEFAULT_UNSCHEDULED_DAILY_LIMIT
    limit = min(max(limit, 1), MAX_UNSCHEDULED_DAILY_LIMIT)
    allow = cfg.get("allow_unscheduled", True)
    if not isinstance(allow, bool):
        allow = True
    return {"unscheduled_daily_limit": limit, "allow_unscheduled": allow}


def merge_appointment_config(org_config, updates: dict) -> dict:
    """Return a copy of *org_config* with *updates* applied to the policy block."""
    current = get_appointment_config(org_config)
    current.update({k: v for k, v in (updates or {}).items() if v is not None})
    merged = dict(org_config or {})
    merged["appointment_config"] = current
    return merged

#:
#: ``bmdc_required`` — a doctor cannot be **activated** (created as active, or
#: moved from inactive to active) without a BMDC registration number.
#:
#: ``bmdc_verification_required`` — activation additionally needs that
#: registration to have been *verified* by staff.
#:
#: Both default to **False**, and that is deliberate rather than lax.  Every
#: doctor row that existed before this release has ``registration_number``
#: ``NULL``; a default of "required" would have made the first save of each of
#: those doctors a 422, i.e. a silent mass lock-out caused by a deploy.  The
#: enforcement is therefore real but **opt-in per organization**: set
#: ``registration_policy`` in the org config (``PATCH
#: /api/v1/orgs/{id}/registration-policy``) and every activation path enforces
#: it from that point on.  Whether the *platform* default should become
#: "required" is a product decision for the owner, not a migration side effect.
DEFAULT_REGISTRATION_POLICY = {
    "bmdc_required": False,
    "bmdc_verification_required": False,
}


def get_registration_policy(org_config=None) -> dict:
    """Read ``registration_policy`` from the Organization ``config`` JSON.

    Unknown or non-boolean values fall back to :data:`DEFAULT_REGISTRATION_POLICY`
    — a malformed config must never silently disable the BMDC rule.
    """
    cfg = (org_config or {}).get("registration_policy") or {}
    policy = dict(DEFAULT_REGISTRATION_POLICY)
    for key in policy:
        value = cfg.get(key)
        if isinstance(value, bool):
            policy[key] = value
    return policy


# ---------------------------------------------------------------------------
# Doctor mobile-number duplicate policy (BR §9.6–§9.8, MP-17)
# ---------------------------------------------------------------------------
#
# BR §9.6–§9.8 state three things, and the difference between them is the whole
# feature:
#
#   6. default doctor mobile-number uniqueness is within an organization;
#   7. Super Admin may allow duplicate doctor mobile numbers within an
#      organization;
#   8. the same mobile number may exist in different organizations.
#
# §9.8 is not a setting — tenancy settles it.  Every duplicate check in the
# doctor service is scoped by ``organization_id``, so a number registered at one
# facility can never block the same number at another, and this module has no
# say in that.  §9.6 and §9.7 are one switch: **unique by default, duplicates
# only where a platform administrator has allowed them**, stored in the
# organization config JSON the way every other facility policy in this file is:
#
#     {
#       "doctor_mobile_policy": {
#         "allow_duplicate_mobile": false,
#         "updated_at": "...", "updated_by": "..."
#       }
#     }
#
# The fallback is *enforced uniqueness*, and a stored value that is not a
# boolean is ignored rather than coerced: a malformed configuration block must
# never turn a uniqueness rule off.
#
# **Prospective only.**  Flipping the allowance changes no doctor row; it only
# decides whether the next create/update that *would* collide is a 409.  If the
# allowance is withdrawn, numbers that became duplicates while it was on stay in
# place — they are referenced by appointments and by the append-only audit
# trail, so the service does not merge, delete or deactivate doctors to restore
# uniqueness behind the operator's back.

#: The platform default for every organization (BR §9.6: unique within the org).
DEFAULT_DOCTOR_MOBILE_POLICY = {"allow_duplicate_mobile": False}


def get_doctor_mobile_policy(org_config=None) -> dict:
    """Read ``doctor_mobile_policy`` from the Organization ``config`` JSON.

    A missing, unknown or non-boolean value falls back to
    :data:`DEFAULT_DOCTOR_MOBILE_POLICY` — uniqueness stays on unless somebody
    with the authority to do so turned it off.
    """
    if not isinstance(org_config, dict):
        org_config = {}
    block = org_config.get("doctor_mobile_policy")
    if not isinstance(block, dict):
        # A string, list or number here is a corrupt configuration, not a
        # permission: the default (unique) stands.
        block = {}
    policy = dict(DEFAULT_DOCTOR_MOBILE_POLICY)
    value = block.get("allow_duplicate_mobile")
    if isinstance(value, bool):
        policy["allow_duplicate_mobile"] = value
    return policy


def doctor_mobile_must_be_unique(org_config=None) -> bool:
    """Whether a doctor's mobile must be unused *within its organization*.

    The single predicate the doctor service consults on create and update; it
    is deliberately phrased as the *enforcement* question rather than the
    storage question, so a caller cannot accidentally read the raw block and
    forget the default.
    """
    return not get_doctor_mobile_policy(org_config)["allow_duplicate_mobile"]


def merge_doctor_mobile_policy(org_config, updates: dict) -> dict:
    """Return a copy of *org_config* with the doctor-mobile block updated."""
    current = get_doctor_mobile_policy(org_config)
    current.update({k: v for k, v in (updates or {}).items() if v is not None})
    merged = dict(org_config or {})
    merged["doctor_mobile_policy"] = current
    return merged


# ---------------------------------------------------------------------------
# Doctor queue-calling (QUE-006 / DEV-1, owner decision D)
# ---------------------------------------------------------------------------
#
# Calling a patient forward is front-desk work in the role matrix: ``call``
# requires ``queue.manage``, which the ``doctor`` role does not hold and which is
# not delegable.  A doctor-only facility has no front desk, so the product rule
# is that *the doctor calls their own patients* — but only where the
# organisation says so, because in a hospital a doctor calling the queue behind
# the front desk's back would be an operational defect, not a feature.
#
# The setting therefore lives in the organization config JSON:
#
#     {
#       "queue_calling_config": {
#         "doctor_queue_calling_enabled": true,
#         "updated_at": "...", "updated_by": "..."
#       }
#     }
#
# and the *default* depends on whether the organisation is a doctor-only
# facility.  ``organizations.facility_type`` is the only facility
# classification the platform has, so it is what the default is derived from —
# a value the product owner registers below gets the approved default, and
# everything else keeps the safe one (disabled).
#
# A value that is not a boolean is ignored rather than coerced: a malformed
# configuration block must never switch a privilege on.
#
# **Open product requirement (owner decision D).** No doctor-only facility type
# exists in the data today: the column's default is ``"hospital"`` and the only
# other value anywhere in the tree is ``"clinic"`` (tests, seeds).  Neither means
# "one doctor, no front desk" — a clinic can have several doctors and a
# receptionist.  Rather than invent a classifier (counting doctors, testing for
# a receptionist row), the approved set below is empty, so every organisation
# defaults to **disabled** until the product owner names the facility type.  The
# approved default then takes effect by adding one value here; no other code
# changes.

#: Facility types that are doctor-only facilities, and therefore get the
#: approved "doctor queue-calling enabled" default.  Empty pending the product
#: owner's facility-type decision — see the block comment above.
DOCTOR_ONLY_FACILITY_TYPES: tuple[str, ...] = ()

#: The default for every organisation that is not a doctor-only facility.
DOCTOR_QUEUE_CALLING_DEFAULT = False


def doctor_queue_calling_default(facility_type=None) -> bool:
    """The approved default for an organisation of *facility_type*."""
    value = facility_type if isinstance(facility_type, str) else ""
    if value.strip().lower() in DOCTOR_ONLY_FACILITY_TYPES:
        return True
    return DOCTOR_QUEUE_CALLING_DEFAULT


def get_queue_calling_config(org_config=None, facility_type=None) -> dict:
    """Read the effective doctor queue-calling policy for one organisation.

    ``doctor_queue_calling_enabled`` is the value enforcement uses: the stored
    override when it is a boolean, otherwise the facility-type default.
    ``default_doctor_queue_calling_enabled`` is returned alongside it so an
    administrator can see *why* the current value is what it is.
    """
    cfg = (org_config or {}).get("queue_calling_config") or {}
    default = doctor_queue_calling_default(facility_type)
    stored = cfg.get("doctor_queue_calling_enabled")
    enabled = stored if isinstance(stored, bool) else default
    return {
        "doctor_queue_calling_enabled": enabled,
        "default_doctor_queue_calling_enabled": default,
        "facility_type": (facility_type or "") if isinstance(facility_type, str)
        else "",
    }


def merge_queue_calling_config(org_config, updates: dict) -> dict:
    """Return a copy of *org_config* with the queue-calling block updated."""
    merged = dict(org_config or {})
    block = dict(merged.get("queue_calling_config") or {})
    block.update({k: v for k, v in (updates or {}).items() if v is not None})
    merged["queue_calling_config"] = block
    return merged
