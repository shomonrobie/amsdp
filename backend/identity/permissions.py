"""RBAC permission matrix — BR §8 FINALIZED.

Keys: role → list of resource patterns.
- "*" grants all resources.
- "patient.*" grants all patient operations.
- Specific: "patient.read", "appointment.create", etc.
"""

PERMISSIONS: dict[str, list[str]] = {
    "super_admin": ["*"],
    "org_admin": [
        "org.manage", "branch.manage", "staff.manage",
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
        "queue.view", "queue.reorder",
    ],
    "doctor": [
        "patient.read", "patient.search",
        "schedule.read", "appointment.read", "queue.view",
    ],
    "assistant": [
        "patient.read", "patient.search",
        "appointment.read", "queue.view",
    ],
}

def check(resource: str, role: str) -> bool:
    """Return True if ``role`` has access to ``resource``."""
    perms = PERMISSIONS.get(role, [])
    if "*" in perms:
        return True
    return any(
        resource == p or resource.startswith(p.rstrip("*"))
        for p in perms
    )