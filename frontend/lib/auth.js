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

export function can(perm) {
  const u = getUser();
  if (!u.role) return false;
  if (u.role === 'super_admin') return true;
  const perms = {
    super_admin: ['*'],
    org_admin: ['org.manage', 'staff.manage', 'patient.*', 'doctor.*', 'schedule.*', 'appointment.*', 'queue.*', 'audit.read', 'queue.consult',
      // AMSDP-FACILITY-DOCTOR-01 — floors / departments / rooms / specialities
      'facility.read', 'facility.manage'],
    branch_admin: ['staff.read', 'patient.*', 'doctor.*', 'schedule.*', 'appointment.*', 'queue.*', 'audit.read', 'queue.consult',
      'facility.read', 'facility.manage'],
    receptionist: ['patient.create', 'patient.read', 'appointment.create', 'appointment.modify', 'queue.view', 'queue.reorder', 'queue.checkin', 'queue.manage',
      // Sequence 3 / BR §27A — mirrors backend/common/permissions.py
      'queue.recover', 'queue.reposition',
      // Read-only facility access: a receptionist sees which rooms exist when booking.
      'facility.read'],
    doctor: ['patient.read', 'schedule.read', 'appointment.read', 'queue.view', 'queue.consult',
      // Sequence 3 / BR §27A.1 + §27A.3 — same-queue recovery only, no queue.manage
      'queue.recover', 'queue.reposition',
      'facility.read'],
    assistant: ['patient.read', 'appointment.read', 'queue.view', 'facility.read'],
  }[u.role] || [];
  if (perms.includes('*')) return true;
  return perms.some(p => perm === p || (p.endsWith('.*') && perm.startsWith(p.slice(0, -1))));
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