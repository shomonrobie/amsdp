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
        "staff.read", "staff.manage", "audit.read",
        # --- clinic capability namespaces (tenant support), no wider ---------
        "patient.*", "doctor.*", "schedule.*", "appointment.*", "queue.*",
    ],
    "org_admin": [
        "org.create", "org.read",
        "org.manage", "branch.manage", "staff.read", "staff.manage",
        "patient.*", "doctor.*", "schedule.*",
        "appointment.*", "queue.*", "audit.read",
    ],
    "branch_admin": [
        "branch.read", "staff.read",
        "patient.*", "doctor.*", "schedule.*",
        "appointment.*", "queue.*", "audit.read",
    ],
    "receptionist": [
        "patient.create", "patient.read", "patient.search",
        "appointment.create", "appointment.read", "appointment.modify",
        "queue.view", "queue.reorder", "queue.checkin", "queue.manage",
        # Sequence 3 / BR §27A: staff-confirmed missed-turn recovery.
        "queue.recover", "queue.reposition",
    ],
    "doctor": [
        "patient.read", "patient.search",
        "schedule.read", "appointment.read", "queue.view", "queue.consult",
        # Sequence 3 / BR §27A.1 + §27A.3: an authorized doctor may confirm a
        # missed turn and reposition within the same queue. This does NOT grant
        # queue.manage (cancel / no-show) or queue.reorder (bulk reorder).
        "queue.recover", "queue.reposition",
    ],
    "assistant": [
        "patient.read", "patient.search",
        "appointment.read", "queue.view",
    ],
}


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