"""AMSDP RBAC permission matrix — BR §8 FINALIZED.

Shared by all services.  The identity/permissions.py module re-exports
these for backward compatibility.

Platform administration (owner decision Q-1, 2026-11-12)
-------------------------------------------------------
``super_admin`` used to hold the bare wildcard ``"*"``, which granted every
string ever passed to :func:`check` — including permissions that do not exist,
and including privileges invented by a future caller.  Q-1 replaces it with an
explicit, reviewable list:

* :data:`PLATFORM_CAPABILITIES` — capabilities that **only** the platform
  administrator holds.  They are the approved platform-administration purpose:
  maintain the platform and support tenants across organizations.
* the clinic capability namespaces (``patient.*``, ``doctor.*``, ``schedule.*``,
  ``appointment.*``, ``queue.*``) plus the concrete administrative
  capabilities (organization / branch / staff / audit) that already exist in
  the matrix.  Nothing is granted that is not already granted to some
  organization-level role, so this is *not* an expansion of authority; it is
  the same vocabulary, enumerated.

An unknown resource is therefore denied for every role, ``super_admin``
included.  A bare ``"*"`` is no longer honoured by :func:`check`.
"""

#: Capabilities reserved for platform administration (Q-1).  No other role may
#: hold these; ``common/auth.py`` and the audit read path use them to decide
#: whether a caller may act outside its own organization.
PLATFORM_CAPABILITIES: tuple[str, ...] = (
    # Maintain the platform itself (tenant provisioning, platform operations).
    "platform.admin",
    # Authorized cross-organization access for tenant support and incident work.
    "platform.cross_org",
)

PERMISSIONS: dict[str, list[str]] = {
    "super_admin": [
        # --- platform administration, this role only (Q-1) -------------------
        *PLATFORM_CAPABILITIES,
        # --- administrative capabilities already in the matrix --------------
        "org.create", "org.read", "org.manage",
        "branch.read", "branch.manage",
        "facility.read", "facility.manage",
        # AMSDP-SYMPTOM-01: the bilingual symptom catalogue is organization
        # configuration like the facility tree — reading it is what the booking
        # form does, managing it (adding/retiring entries) is administrative.
        "symptom.read", "symptom.manage",
        "staff.read", "staff.manage", "audit.read",
        # --- clinic capability namespaces (tenant support), no wider ---------
        "patient.*", "doctor.*", "schedule.*", "appointment.*", "queue.*",
    ],
    "org_admin": [
        "org.create", "org.read",
        "org.manage", "branch.manage",
        # AMSDP-FACILITY-DOCTOR-01: floors / departments / rooms / specialities
        # are organization configuration, so they get their own capability.
        # BMDC verification is *not* a new capability: it is gated on the
        # existing "doctor.manage" (inside the "doctor.*" namespace below), so
        # the matrix gains no invented privilege.
        "facility.read", "facility.manage",
        # AMSDP-SYMPTOM-01 — mirrors super_admin, and is what lets an
        # administrator retrieve retired catalogue entries for review.
        "symptom.read", "symptom.manage",
        "staff.read", "staff.manage",
        # BR §54 / PO-RBAC-02: patient.update is explicit — org_admin may modify
        # patient demographics and operational registration information.
        "patient.read", "patient.search", "patient.create", "patient.update",
        "doctor.*", "schedule.*",
        "appointment.*", "queue.*", "audit.read",
    ],
    "branch_admin": [
        "branch.read", "facility.read", "facility.manage", "staff.read",
        # AMSDP-SYMPTOM-01 — a branch administrator curates the branch's wording.
        "symptom.read", "symptom.manage",
        # BR §54 / PO-RBAC-02: patient.update is explicit — branch_admin may modify
        # patient demographics and operational registration information.
        "patient.read", "patient.search", "patient.create", "patient.update",
        "doctor.*", "schedule.*",
        "appointment.*", "queue.*", "audit.read",
    ],
    "receptionist": [
        "patient.create", "patient.read", "patient.search",
        # Read-only facility access: a receptionist must be able to see which
        # rooms exist at this branch when booking, and must not be able to
        # create or retire them.
        "facility.read",
        # AMSDP-SYMPTOM-01: reading the catalogue is part of taking a booking;
        # nothing here grants the receptionist the ability to change it.
        "symptom.read",
        "appointment.create", "appointment.read", "appointment.modify",
        # AMSDP-APPT-OWNER-DECISIONS-01 (Q3): check-in is its own capability, not
        # a side effect of appointment.modify.  The front desk holds it; a doctor
        # holds it for their own patients without gaining modify.
        "appointment.check_in",
        # Q1: the front desk may accept an outside-session patient, but only with
        # a recorded reason, under the organization's unscheduled limit, and with
        # an audit event — the capability is separate so it can be withdrawn.
        "appointment.create_unscheduled",
        "queue.view", "queue.reorder", "queue.checkin", "queue.manage",
        # Sequence 3 / BR §27A: staff-confirmed missed-turn recovery.
        "queue.recover", "queue.reposition",
    ],
    "doctor": [
        "patient.read", "patient.search",
        "facility.read",
        # AMSDP-SYMPTOM-01: a doctor reads what the receptionist recorded.
        "symptom.read",
        "schedule.read", "appointment.read", "queue.view", "queue.consult",
        # AMSDP-APPT-OWNER-DECISIONS-01 (Q1/Q3, Scenario A): a doctor working
        # without a receptionist registers and checks in their own walk-in
        # patients.  Their own, because every route applying these capabilities
        # also enforces ``can_access_doctor`` against the explicit assignment —
        # which fails closed.  ``appointment.modify`` is deliberately NOT granted:
        # cancel, reschedule and transfer stay front-desk work.
        "appointment.create", "appointment.check_in",
        "appointment.create_unscheduled",
        # Sequence 3 / BR §27A.1 + §27A.3: an authorized doctor may confirm a
        # missed turn and reposition within the same queue. This does NOT grant
        # queue.manage (cancel / no-show) or queue.reorder (bulk reorder).
        "queue.recover", "queue.reposition",
    ],
    "assistant": [
        "patient.read", "patient.search",
        "facility.read",
        # AMSDP-SYMPTOM-01: read-only, like the rest of the assistant matrix.
        "symptom.read",
        "appointment.read", "queue.view",
        # AMSDP-APPT-OWNER-DECISIONS-01 (Q3): an assistant may check in patients
        # for the doctor(s) they are assigned to, and for nobody else.  The
        # assignment check is enforced by the check-in routes, not by this list.
        "appointment.check_in",
    ],
}

#: Capabilities an administrator may grant to an individual staff member, over
#: and above their role (owner decisions Q1/Q4).
#:
#: Deliberately a closed, short list.  A grant can only *widen* authority that
#: already exists in the matrix, never invent a new kind of access, so nothing
#: here can hand out ``appointment.modify``, ``org.manage`` or ``audit.read``
#: to a role that was never meant to hold it.
DELEGABLE_CAPABILITIES: tuple[str, ...] = (
    # Q4: central-reception staff book into another branch of the same
    # organization.  Does not grant reads, cancellation or patient records
    # outside the branch — those stay ``branch_accessible`` decisions.
    "appointment.book_cross_branch",
    # Q1: accept an outside-session patient through the override workflow.
    "appointment.create_unscheduled",
    # Q3: check a patient in without any other modification authority.
    "appointment.check_in",
)

# PO-RBAC-05 / O-SaaS-8: Platform roles — distinct from tenant roles.
# Platform roles hold only platform.* capabilities; they do NOT automatically
# receive tenant business-data access.  A tenant org_admin is NOT a platform
# administrator by default.
PLATFORM_ROLES: dict[str, list[str]] = {
    "platform_admin": [
        # Full platform administration (tenant provisioning, platform operations).
        *PLATFORM_CAPABILITIES,
        # Platform-level audit read.
        "audit.read",
    ],
    "platform_ops": [
        # Platform operations: tenant support, incident response.
        "platform.cross_org",
        # Platform-level audit read.
        "audit.read",
    ],
    "platform_support": [
        # Limited platform support: read-only tenant access for support.
        "platform.cross_org",
        "audit.read",
    ],
}

# PO-RBAC-03: Role hierarchy for self-escalation prevention.
# Higher numbers = more privileged.  super_admin is the top tenant role.
# Platform roles are a separate authorization domain (not compared in hierarchy).
ROLE_HIERARCHY: dict[str, int] = {
    "assistant": 1,
    "doctor": 2,
    "receptionist": 3,
    "branch_admin": 4,
    "org_admin": 5,
    "super_admin": 6,
}


def role_level(role: str) -> int:
    """Return the privilege level of *role*, or 0 for unknown roles."""
    return ROLE_HIERARCHY.get(role, 0)


def can_grant_role(grantor_role: str, target_role: str) -> bool:
    """Return True if *grantor_role* may assign *target_role* to another user.

    A user cannot grant a role at or above their own level, except
    super_admin who can grant any role.
    """
    if grantor_role == "super_admin":
        return True
    return role_level(target_role) < role_level(grantor_role)


def check(resource: str, role: str) -> bool:
    """Return True if *role* has access to *resource*.

    Matching is exact, or by the ``<namespace>.*`` pattern a role holds
    (``patient.*`` grants ``patient.read``).  A bare ``"*"`` is deliberately
    **not** honoured: an unknown resource is denied for every role, including
    the platform administrator, whose capabilities are enumerated in
    :data:`PERMISSIONS` (owner decision Q-1).
    """
    perms = PERMISSIONS.get(role, [])
    return any(
        resource == p or (p.endswith("*") and resource.startswith(p[:-1]))
        for p in perms
    )

def check_granted(resource: str, role: str, granted=()) -> bool:
    """Return True if *role* — or an explicit grant held by this user — allows it.

    Owner decisions Q1/Q4 add staff-level capability grants on top of the role
    matrix (:class:`common.models.StaffCapabilityGrant`).  A grant can only
    *add* to what the role already holds, so this is the union of the two, never
    a replacement: revoking the grant restores exactly the role authority.
    """
    if check(resource, role):
        return True
    return resource in set(granted or ())
