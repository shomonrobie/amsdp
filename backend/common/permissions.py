"""AMSDP RBAC permission matrix — BR §8 FINALIZED.

Shared by all services.  The identity/permissions.py module re-exports
these for backward compatibility.
"""

PERMISSIONS: dict[str, list[str]] = {
    "super_admin": ["*"],
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
    """Return True if *role* has access to *resource*."""
    perms = PERMISSIONS.get(role, [])
    if "*" in perms:
        return True
    return any(
        resource == p or resource.startswith(p.rstrip("*"))
        for p in perms
    )