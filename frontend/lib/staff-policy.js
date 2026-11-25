/* MP-19 / MP-20 — the client-side half of the staff administration rules.
 *
 * None of this is an authorization boundary.  The server decides every request:
 * ``staff.manage`` for writes, organization-administrator authority for grants,
 * ``can_grant_role`` for roles, ``staff.read`` for the catalogue.  These helpers
 * decide only what the screen *offers*, so the page carries no private copy of
 * the role ladder and the rules can be asserted without a browser
 * (``tests/staff-policy.test.mjs``).
 *
 * ``ROLE_LEVEL`` mirrors ``backend/common/permissions.py`` (``ROLE_HIERARCHY``).
 * The duplication is deliberate and pinned: if the two ever disagree the screen
 * offers a role the server refuses, which the browser suite catches.
 */

export const ROLE_LEVEL = Object.freeze({
  assistant: 1,
  doctor: 2,
  receptionist: 3,
  branch_admin: 4,
  org_admin: 5,
  super_admin: 6,
});

/** Least privileged first — the order a role picker should read in. */
export const ROLE_ORDER = Object.freeze(
  Object.keys(ROLE_LEVEL).sort((a, b) => ROLE_LEVEL[a] - ROLE_LEVEL[b]));

/** Roles whose scope comes from a branch; the others are organization-wide. */
export const BRANCH_SCOPED_ROLES = Object.freeze(
  ['receptionist', 'doctor', 'assistant', 'branch_admin']);

/** i18n keys for the role names, so no screen hard-codes an English label. */
export const ROLE_KEYS = Object.freeze({
  assistant: 'roleAssistant',
  doctor: 'roleDoctor',
  receptionist: 'roleReceptionist',
  branch_admin: 'roleBranchAdmin',
  org_admin: 'roleOrgAdmin',
  super_admin: 'roleSuperAdmin',
});

export function roleLabelKey(role) {
  return ROLE_KEYS[role] || 'roleLabel';
}

export function roleLevel(role) {
  return ROLE_LEVEL[role] || 0;
}

/** A caller may assign a role below their own; super_admin may assign any. */
export function canOfferRole(actorRole, targetRole) {
  if (!ROLE_LEVEL[targetRole]) return false;
  if (actorRole === 'super_admin') return true;
  return roleLevel(targetRole) < roleLevel(actorRole);
}

export function grantableRoles(actorRole) {
  return ROLE_ORDER.filter((role) => canOfferRole(actorRole, role));
}

/** Only an organization administrator may grant or revoke (backend Q4 rule). */
export function mayGrantCapabilities(actorRole) {
  return actorRole === 'org_admin' || actorRole === 'super_admin';
}

export function needsBranch(role) {
  return BRANCH_SCOPED_ROLES.includes(role);
}

/* The delegable set itself comes from the server
 * (``GET /api/v1/staff/capabilities``); only the labels live here. */
export const CAPABILITY_LABEL_KEYS = Object.freeze({
  'appointment.book_cross_branch': 'capBookCrossBranch',
  'appointment.create_unscheduled': 'capCreateUnscheduled',
  'appointment.check_in': 'capCheckIn',
});

export function capabilityLabelKey(capability) {
  return CAPABILITY_LABEL_KEYS[capability] || capability;
}

/** PO-RBAC-01: several doctors are possible; the legacy single id is a fallback. */
export function assignedDoctorIds(user) {
  if (!user) return [];
  if (Array.isArray(user.doctor_ids)) return user.doctor_ids.filter(Boolean);
  return user.doctor_id ? [user.doctor_id] : [];
}

export function isActiveStatus(status) {
  return (status || 'active') === 'active';
}

/** Pre-flight for the create form.  The server repeats every rule. */
export function validateNewStaff(form, { branchRequired = false } = {}) {
  const fields = [];
  if (!String(form.username || '').trim()) fields.push('username');
  if (!String(form.display_name || '').trim()) fields.push('display_name');
  if (!ROLE_LEVEL[form.role]) fields.push('role');
  if (branchRequired && !String(form.branch_id || '').trim()) fields.push('branch_id');
  const passwordTooShort = String(form.password || '').length < 8;
  return { ok: fields.length === 0 && !passwordTooShort, fields, passwordTooShort };
}

export function staffMatchesFilter(staff, { q = '', role = '', status = '' } = {}) {
  const needle = String(q || '').trim().toLowerCase();
  if (needle) {
    const haystack = [staff.username, staff.display_name, staff.mobile, staff.email]
      .filter(Boolean).map((value) => String(value).toLowerCase());
    if (!haystack.some((value) => value.includes(needle))) return false;
  }
  if (role && staff.role !== role) return false;
  if (status && (staff.status || 'active') !== status) return false;
  return true;
}
