/* Queue history helpers — MP-24.
 *
 * The history screen reads `GET /api/v1/queue/history`, whose query contract
 * already exists (`queuing/main.py::queue_history`): `doctor_id` and `date` are
 * required, `status` and `branch_id` optional.  Building that query in one place
 * keeps the page from inventing parameters the server ignores — a silently
 * dropped filter is worse than no filter, because the table then claims a
 * narrower answer than it returned.
 *
 * `summarise` counts what the server sent.  It never re-classifies an entry: a
 * `skipped` row is counted as skipped, not folded into `waiting`, so the tally
 * cannot disagree with the rows beneath it.
 */

/** The queue statuses, each with the shared label key that names it. */
export const STATUS_OPTIONS = [
  { value: 'waiting', labelKey: 'waitingKey' },
  { value: 'called', labelKey: 'calledKey' },
  { value: 'in_consultation', labelKey: 'inConsultationKey' },
  { value: 'skipped', labelKey: 'skippedKey' },
  { value: 'completed', labelKey: 'completedKey' },
  { value: 'cancelled', labelKey: 'cancelledKey' },
  { value: 'no_show', labelKey: 'noShowKey' },
];

/**
 * The request path for one day of one doctor's history.
 *
 * Empty optional values are omitted rather than sent as `""`: the server treats
 * an absent `branch_id` as "the caller's own branch" and an absent `status` as
 * "every status", and an empty string is neither.
 */
export function historyQuery({ doctorId, day, status, branchId } = {}) {
  const params = [];
  if (doctorId) params.push('doctor_id=' + encodeURIComponent(doctorId));
  if (day) params.push('date=' + encodeURIComponent(day));
  if (status) params.push('status=' + encodeURIComponent(status));
  if (branchId) params.push('branch_id=' + encodeURIComponent(branchId));
  return '/api/v1/queue/history?' + params.join('&');
}

/** Count entries per status.  Unknown statuses are counted under their own name. */
export function summarise(rows) {
  const counts = {};
  for (const row of rows || []) {
    const key = row && row.status ? row.status : 'unknown';
    counts[key] = (counts[key] || 0) + 1;
  }
  return counts;
}
