/* AMSDP shared auth/session utilities. */
export function getUser() {
  if (typeof window === 'undefined') return {};
  try { return JSON.parse(sessionStorage.getItem('amsdp_user') || '{}'); }
  catch (e) { return {}; }
}

export function getToken() {
  if (typeof window === 'undefined') return '';
  return sessionStorage.getItem('amsdp_token') || '';
}

export function isAuthenticated() {
  return !!getUser().id;
}

/* The client-side mirror of `backend/common/permissions.py::PERMISSIONS`.
 *
 * It exists so the interface can hide what the server would refuse — it is never
 * the boundary.  It is therefore kept *identical* to the server matrix, entry for
 * entry: a screen that asks `can('org.read')` must get the same answer the route
 * would give, or the menu lies in one direction or the other.  The MP-04
 * voice-pack screen is exactly that case: it was gated on `org.read`, which this
 * mirror withheld from `org_admin` while the server granted it, so the one role
 * that may configure a facility's voice saw a permission refusal.
 *
 * `tests/permissions-mirror.test.mjs` parses the Python matrix and fails when the
 * two drift, so the next divergence is caught here rather than in a browser.
 */
export const ROLE_PERMISSIONS = Object.freeze({
  super_admin: Object.freeze([
    // platform administration, this role only (Q-1)
    'platform.admin', 'platform.cross_org',
    'org.create', 'org.read', 'org.manage',
    'branch.read', 'branch.manage',
    'facility.read', 'facility.manage',
    'symptom.read', 'symptom.manage',
    'staff.read', 'staff.manage', 'audit.read',
    // clinic capability namespaces, no wider than the server grants
    'patient.*', 'doctor.*', 'schedule.*', 'appointment.*', 'queue.*',
  ]),
  org_admin: Object.freeze([
    'org.create', 'org.read', 'org.manage', 'branch.manage',
    'facility.read', 'facility.manage',
    'symptom.read', 'symptom.manage',
    'staff.read', 'staff.manage',
    'patient.read', 'patient.search', 'patient.create', 'patient.update',
    'doctor.*', 'schedule.*', 'appointment.*', 'queue.*', 'audit.read',
  ]),
  branch_admin: Object.freeze([
    'branch.read', 'facility.read', 'facility.manage', 'staff.read',
    'symptom.read', 'symptom.manage',
    'patient.read', 'patient.search', 'patient.create', 'patient.update',
    'doctor.*', 'schedule.*', 'appointment.*', 'queue.*', 'audit.read',
  ]),
  receptionist: Object.freeze([
    'patient.create', 'patient.read', 'patient.search',
    'facility.read', 'symptom.read',
    'appointment.create', 'appointment.read', 'appointment.modify',
    'appointment.check_in', 'appointment.create_unscheduled',
    'queue.view', 'queue.reorder', 'queue.checkin', 'queue.manage',
    'queue.recover', 'queue.reposition',
  ]),
  doctor: Object.freeze([
    'patient.read', 'patient.search', 'facility.read', 'symptom.read',
    'schedule.read', 'appointment.read', 'queue.view', 'queue.consult',
    'appointment.create', 'appointment.check_in', 'appointment.create_unscheduled',
    'queue.recover', 'queue.reposition',
  ]),
  assistant: Object.freeze([
    'patient.read', 'patient.search', 'facility.read', 'symptom.read',
    'appointment.read', 'queue.view', 'appointment.check_in',
  ]),
});

/**
 * Does *user* hold *perm*?  Pure, so a test can compare it with the server matrix
 * without a browser session.
 */
export function hasPermission(user, perm) {
  const role = (user && user.role) || '';
  const perms = ROLE_PERMISSIONS[role];
  if (!perms) return false;
  return perms.some((p) => perm === p
    || (p.endsWith('.*') && perm.startsWith(p.slice(0, -1))));
}

export function can(perm, user) {
  return hasPermission(user || getUser(), perm);
}

export async function apiFetch(path, opts = {}) {
  const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
  const token = getToken();
  if (token) headers.Authorization = 'Bearer ' + token;
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  if (!res.ok) {
    let detail = res.statusText;
    try { const j = await res.json(); detail = j.detail || detail; } catch (e) { /* ignore */ }
    throw Object.assign(new Error(String(detail)), { status: res.status, body: detail });
  }
  return res.json();
}

export function getActiveBranch() {
  if (typeof window === 'undefined') return '';
  const u = getUser();
  const saved = sessionStorage.getItem('amsdp_branch');
  if (saved) return saved;
  return u.branch_id || '';
}

export function setActiveBranch(branchId) {
  if (typeof window === 'undefined') return;
  if (branchId) sessionStorage.setItem('amsdp_branch', branchId);
  else sessionStorage.removeItem('amsdp_branch');
}

export function signOut() {
  sessionStorage.clear();
  if (typeof window !== 'undefined') window.location.href = '/';
}