"""RBAC permission matrix — BR §8 FINALIZED.

Re-exports from common.permissions for backward compatibility.
"""

from common.permissions import PERMISSIONS, check, can_grant_role, role_level, PLATFORM_ROLES  # noqa