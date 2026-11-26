/* Operational reports — BR §43 (MP-23, Product Owner decision PO-11).
 *
 * MP-23's approved scope is *one reporting surface plus one report screen* for the
 * five §43 dimensions. The endpoint (`backend/appointment/reports.py`) does the
 * counting and the scoping; this module only holds the screen's rules, so they can
 * be tested without a browser:
 *
 *  * the query it builds uses the endpoint's own parameter names and never sends a
 *    day *and* a period (the route answers 422 for that);
 *  * the period ceiling is read from the backend constant rather than guessed;
 *  * the headline figures are the ones the backend publishes — a figure the server
 *    stops sending would otherwise vanish silently;
 *  * `percent: null` is rendered as "no figure", never as 0%, because a percentage
 *    whose denominator is undefined is not zero;
 *  * every identity the backend claims in `reconciliation` is re-checked here, so
 *    the screen shows "reconciles" only when it actually does.
 *
 * The screen adds no authority: the organisation comes from the token, the branch
 * from the token's scope, and a foreign branch is the route's non-disclosing 404.
 */

/** The endpoint this screen reads. */
export const REPORT_PATH = '/api/v1/reports/operational';

/** The period ceiling, mirroring `reports.MAX_PERIOD_DAYS`. */
export const MAX_PERIOD_DAYS = 366;

/** The five BR §43 dimensions, in the order an operator reads them. */
export const DIMENSIONS = Object.freeze([
  { key: 'appointments', labelKey: 'repDimAppointments' },
  { key: 'status', labelKey: 'repDimStatus' },
  { key: 'walkIns', labelKey: 'repDimWalkIns' },
  { key: 'queue', labelKey: 'repDimQueue' },
  { key: 'utilisation', labelKey: 'repDimUtilisation' },
]);

/**
 * The headline figures, in the order `reports.HEADLINE` emits them, plus
 * `present`. `present` is not one of the four BR §43 counts: it is the
 * in-facility statuses reported separately so a reader can get from the headline
 * figures back to the total without subtracting.
 */
export const HEADLINE_ORDER = Object.freeze([
  'booked', 'completed', 'cancelled', 'no_show', 'present',
]);

/** Headline figure -> i18n key. */
export const HEADLINE_KEYS = Object.freeze({
  booked: 'repBooked',
  completed: 'repCompleted',
  cancelled: 'repCancelled',
  no_show: 'repNoShow',
  present: 'repPresent',
});

/** Stored appointment status -> i18n key.  Unknown statuses print as-is. */
export const STATUS_LABELS = Object.freeze({
  BOOKED: 'repStBooked',
  AWAITING_CONFIRMATION: 'repStAwaiting',
  CONFIRMED: 'repStConfirmed',
  CHECKED_IN: 'repStCheckedIn',
  IN_QUEUE: 'repStInQueue',
  IN_CONSULTATION: 'repStInConsultation',
  COMPLETED: 'repStCompleted',
  CANCELLED: 'repStCancelled',
  NO_SHOW: 'repStNoShow',
  RESCHEDULED: 'repStRescheduled',
});

/** Queue entry state -> i18n key. */
export const QUEUE_STATE_LABELS = Object.freeze({
  waiting: 'repQsWaiting',
  called: 'repQsCalled',
  in_consultation: 'repQsInConsultation',
  skipped: 'repQsSkipped',
  completed: 'repQsCompleted',
  cancelled: 'repQsCancelled',
  no_show: 'repQsNoShow',
});

/** Queue metrics, in the order the endpoint publishes them. */
export const QUEUE_METRICS = Object.freeze([
  { key: 'entries', labelKey: 'repQueueEntries' },
  { key: 'calls', labelKey: 'repQueueCalls' },
  { key: 'transitions', labelKey: 'repQueueTransitions' },
  { key: 'avg_wait_minutes', labelKey: 'repQueueWait' },
  { key: 'avg_service_minutes', labelKey: 'repQueueService' },
]);

/** `YYYY-MM-DD` for a `Date`, in the operator's own timezone. */
export function isoDay(value) {
  if (!value) return '';
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function daysBetween(from, to) {
  if (!from || !to) return 0;
  const a = new Date(from + 'T00:00:00Z');
  const b = new Date(to + 'T00:00:00Z');
  if (Number.isNaN(a.getTime()) || Number.isNaN(b.getTime())) return 0;
  return Math.round((b - a) / 86400000) + 1;
}

/** Is this range longer than the route will answer? */
export function periodTooLong(from, to) {
  return daysBetween(from, to) > MAX_PERIOD_DAYS;
}

/** Is this range inverted (`from` after `to`)? */
export function periodInverted(from, to) {
  return !!from && !!to && daysBetween(from, to) < 1;
}

/**
 * The query string for one report request.
 *
 * `mode` decides which date parameters exist: `day` sends `date`, `range` sends
 * `from_date`/`to_date`, and neither sends both — the route refuses that with 422,
 * and a screen that can produce a refused request is a screen that failed a click.
 * Empty filters are omitted rather than sent blank.
 */
export function reportQuery(params) {
  const p = params || {};
  const parts = [];
  const add = (name, value) => {
    if (value === undefined || value === null || value === '') return;
    parts.push(encodeURIComponent(name) + '=' + encodeURIComponent(value));
  };
  if (p.mode === 'range') {
    add('from_date', p.from);
    add('to_date', p.to);
  } else {
    add('date', p.day);
  }
  add('branch_id', p.branchId);
  add('doctor_id', p.doctorId);
  return REPORT_PATH + (parts.length ? '?' + parts.join('&') : '');
}

/** A percentage, or the "no figure" dash when the denominator is undefined. */
export function percentText(value) {
  if (value === null || value === undefined || value === '') return '—';
  const number = Number(value);
  return Number.isFinite(number) ? number + '%' : '—';
}

/** A minutes figure, or the dash when the server had nothing to average. */
export function minutesText(value) {
  if (value === null || value === undefined || value === '') return '—';
  const number = Number(value);
  return Number.isFinite(number) ? String(number) : '—';
}

/**
 * Status counts as rows, in the **server's** order.
 *
 * The endpoint returns `status_counts` already ordered by the lifecycle
 * (`reports.LIFECYCLE`) and unsuppressed, so the screen must not re-sort or
 * re-filter it: doing either here would make the screen's order differ from the
 * report the figures came from.
 */
export function statusRows(statusCounts) {
  return Object.entries(statusCounts || {}).map(([status, count]) => ({
    status,
    labelKey: STATUS_LABELS[status] || '',
    count,
  }));
}

/** Queue states as rows, in the server's order. */
export function queueStateRows(byStatus) {
  return Object.entries(byStatus || {}).map(([state, count]) => ({
    state,
    labelKey: QUEUE_STATE_LABELS[state] || '',
    count,
  }));
}

/**
 * Re-check every identity the endpoint claims in `reconciliation`.
 *
 * Returns `{ ok, problems }` where `problems` names the identities that do *not*
 * hold. The screen renders "reconciles" only from this answer, so the claim is
 * computed from the payload rather than copied from the API's intent.
 */
export function reconciles(body) {
  const rec = (body && body.reconciliation) || null;
  if (!rec) return { ok: false, problems: ['reconciliation'] };
  const problems = [];
  const check = (name, left, right) => {
    if (left === undefined || right === undefined) { problems.push(name); return; }
    if (Number(left) !== Number(right)) problems.push(name);
  };
  check('status_sum', rec.status_sum, rec.appointments_total);
  check('by_day_sum', rec.by_day_sum, rec.appointments_total);
  check('by_doctor_sum', rec.by_doctor_sum, rec.appointments_total);
  check('by_branch_sum', rec.by_branch_sum, rec.appointments_total);
  check('booking_sources_sum', rec.booking_sources_sum, rec.appointments_total);
  check('queue_status_sum', rec.queue_status_sum, rec.queue_entries);
  const appointments = (body && body.appointments) || {};
  check('appointments_total', rec.appointments_total, appointments.total);
  const queue = (body && body.queue_activity) || {};
  check('queue_entries', rec.queue_entries, queue.entries);
  return { ok: problems.length === 0, problems };
}

/** Is there nothing to report for the requested period? */
export function isEmptyReport(body) {
  const appointments = (body && body.appointments) || {};
  const queue = (body && body.queue_activity) || {};
  return (appointments.total || 0) === 0 && (queue.entries || 0) === 0;
}

/**
 * Who the figures cover, in the caller's terms.
 *
 * `branch_id` is the scope the **server** resolved (the token's branch for a
 * branch-scoped principal, or the requested one), and `requested_branch_id` is
 * what the screen asked for — shown so a branch-scoped operator can see that their
 * view is narrowed rather than silently smaller.
 */
export function scopeOf(body) {
  const b = body || {};
  return {
    from: b.from || '',
    to: b.to || '',
    facilityToday: b.facility_today || '',
    branchId: b.branch_id || '',
    requestedBranchId: b.requested_branch_id || '',
    doctorId: b.doctor_id || '',
    narrowed: !!b.branch_id && !b.requested_branch_id,
  };
}

/** The utilisation figures as rows, with `percent` kept null when undefined. */
export function utilisationRows(utilisation) {
  return ((utilisation && utilisation.by_doctor) || []).map((row) => ({
    doctorId: row.doctor_id,
    capacity: row.capacity,
    claimed: row.claimed,
    unscheduled: row.unscheduled,
    percent: row.percent === undefined ? null : row.percent,
  }));
}
