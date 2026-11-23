"""AMSDP org/branch queue configuration helpers (default-disabled).

Reads ``queue_config`` from the Organization ``config`` JSON:

    {
      "queue_config": {
        "walk_in_reserve_mode": "percent" | "count",
        "walk_in_reserve_value": int   # percent of capacity, or fixed count
      }
    }

Default: no reservation configured -> behaviour identical to prior releases.
"""


def get_queue_config(org_config=None) -> dict:
    cfg = (org_config or {}).get("queue_config") or {}
    mode = cfg.get("walk_in_reserve_mode")
    if mode not in ("percent", "count"):
        mode = "percent"
    value = int(cfg.get("walk_in_reserve_value") or 0)
    return {"walk_in_reserve_mode": mode,
            "walk_in_reserve_value": max(value, 0)}


def reserved_for_capacity(capacity: int, org_config=None) -> int:
    """Number of slots reserved for walk-ins for a capacity of *capacity*."""
    cfg = get_queue_config(org_config)
    value = cfg["walk_in_reserve_value"]
    if value <= 0 or capacity <= 0:
        return 0
    if cfg["walk_in_reserve_mode"] == "count":
        return min(value, capacity)
    return int(round(capacity * value / 100.0))


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
