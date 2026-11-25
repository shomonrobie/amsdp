/* Dashboard rules (MP-22) — the parts that are decisions rather than markup.
 *
 * The screen itself is JSX and this project ships no DOM renderer, so anything
 * that decides *what the dashboard offers* lives here where it can be asserted:
 * which branches the selector may list, which quick actions a role is offered,
 * how a query string is built, and how an audit event becomes a readable row.
 *
 * **None of it is an authorization boundary.** Every figure on the dashboard
 * comes from `/api/v1/dashboard/today`, which derives the tenant and the branch
 * from the token: a branch user who forges `branch_id` in the URL gets the
 * server's non-disclosing 404, not another branch's numbers. Filtering the
 * selector here is a courtesy that avoids offering a choice that will fail.
 */

/** Roles whose reach is the whole organization, so every branch is selectable. */
export const BRANCH_WIDE_ROLES = Object.freeze(['org_admin', 'super_admin']);

/** Roles that live in the queue rather than in scheduling or registration. */
export const QUEUE_ROLES = Object.freeze(['doctor', 'assistant']);

export function mayChooseAnyBranch(user) {
  const role = String((user && user.role) || '');
  return BRANCH_WIDE_ROLES.includes(role);
}

/**
 * The branches this user may pick from.
 *
 * A branch-scoped user is offered their own branch only — and if the roster does
 * not contain it (an archived branch, or a stale roster) the list is empty rather
 * than silently falling back to "all", which is how a selector ends up offering
 * a tenant's entire tree to a front-desk user.
 */
export function selectableBranches(branches, user) {
  const rows = (Array.isArray(branches) ? branches : [])
    .filter((b) => b && (b.status || 'active') === 'active');
  if (mayChooseAnyBranch(user)) return rows;
  const own = String((user && user.branch_id) || '');
  if (!own) return [];
  return rows.filter((b) => String(b.id) === own);
}

/**
 * Navigation shortcuts. They are links, not authority: every target page and
 * every write behind it enforces its own permission, so the only question here
 * is which surfaces are worth one click for this role.
 */
export function quickActionsFor(user) {
  const role = String((user && user.role) || '');
  const all = [
    { href: '/appointments/new', key: 'newAppointment' },
    { href: '/queue', key: 'queue' },
    { href: '/patients', key: 'patients' },
    { href: '/schedules', key: 'schedules' },
  ];
  if (QUEUE_ROLES.includes(role)) {
    return all.filter((a) => a.key === 'queue' || a.key === 'newAppointment');
  }
  return all;
}

/** `/api/v1/dashboard/today?branch_id=…&date=…`, omitting what was not chosen. */
export function dashboardQuery({ branchId, date } = {}) {
  const parts = [];
  if (branchId) parts.push('branch_id=' + encodeURIComponent(branchId));
  if (date) parts.push('date=' + encodeURIComponent(date));
  return parts.length ? '?' + parts.join('&') : '';
}

/** `/api/v1/dashboard/audit?…` for the recent-activity panel. */
export function activityQuery({ branchId, limit } = {}) {
  const parts = ['limit=' + encodeURIComponent(String(limit || 8))];
  if (branchId) parts.push('branch_id=' + encodeURIComponent(branchId));
  return '?' + parts.join('&');
}

/** Actions worth naming in the panel; anything else renders as its own slug. */
export const ACTIVITY_LABELS = Object.freeze({
  'appointment.created': 'newAppointment',
  'appointment.cancelled': 'cancelledT',
  'appointment.rescheduled': 'rescheduledT',
  'appointment.status_change': 'status',
  'queue.enqueue': 'queue',
  'queue.call': 'queue',
  'queue.recall': 'queue',
  'queue.complete': 'completedT',
  'doctor.create': 'doctor',
  'staff.user.create': 'staffT',
  'schedule.updated': 'schedules',
});

/**
 * One audit event as a displayable row.
 *
 * `labelKey` is an i18n key when the action is one we have words for, and the
 * raw action otherwise — an unknown event is shown as itself rather than
 * dropped, because a dashboard that hides activity is worse than one that shows
 * an untranslated action name.
 */
export function activityRow(event) {
  const action = String((event && event.action) || '');
  return {
    action,
    labelKey: ACTIVITY_LABELS[action] || '',
    actor: String((event && event.actor_id) || ''),
    role: String((event && event.actor_role) || ''),
    target: String((event && event.target_id) || ''),
    when: String((event && event.timestamp) || ''),
  };
}

export function activityRows(events) {
  return (Array.isArray(events) ? events : []).map(activityRow);
}

/** A doctor's share of the day, for the queue panel. */
export function perDoctorRows(today, doctorNames) {
  const rows = (today && Array.isArray(today.per_doctor)) ? today.per_doctor : [];
  const names = doctorNames || {};
  return rows
    .map((r) => ({
      doctorId: String(r.doctor_id || ''),
      name: names[String(r.doctor_id || '')] || String(r.doctor_id || ''),
      count: Number(r.count) || 0,
    }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}
