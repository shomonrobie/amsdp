/* MP-10 / BR §25 — the walk-in form's decisions, kept pure.
 *
 * Where a walk-in joins the queue is a **facility setting** now
 * (`queue_config.walk_in_policy`, written through
 * `PUT /api/v1/orgs/{id}/walk-in-config`). The page used to send a policy in
 * every request body, which let one receptionist place a patient by a rule the
 * facility had not chosen — and left BR §25's "Facility Admin selects policy"
 * with no home. This module holds the two client-side decisions so they can be
 * tested without React:
 *
 *   - which policy is in force (read from the server, never assumed), and
 *   - what the `POST /api/v1/queue/enqueue` body may contain: never a policy,
 *     and a position only where the facility's policy asks staff for one.
 *
 * The server still enforces both rules (`queuing.placement`); this file only
 * decides what to show and what to send.
 */

/** The four policies BR §25 approves, in the platform's canonical order. */
export const PLACEMENT_POLICIES = Object.freeze([
  'end_of_queue',
  'first_come',
  'reserved_capacity',
  'staff_placement',
]);

/** The policy under which staff must name the position. */
export const STAFF_PLACEMENT = 'staff_placement';

/**
 * The policy in force, according to the server's view.
 *
 * An unknown or missing value falls back to `end_of_queue`, which is what the
 * server falls back to as well: the form must never *invent* a stricter or
 * looser rule than the one the backend applies.
 *
 * @param {{walk_in_policy?: unknown}} config
 * @returns {string}
 */
export function effectivePolicy(config) {
  const policy = config && typeof config === 'object' ? config.walk_in_policy : '';
  return PLACEMENT_POLICIES.includes(policy) ? policy : 'end_of_queue';
}

/**
 * The i18n key for a policy's human label.
 *
 * Every key this returns must exist in both languages; the test asserts that,
 * so a policy cannot reach the screen as a raw identifier.
 *
 * @param {string} policy
 * @returns {string}
 */
export function policyLabelKey(policy) {
  switch (policy) {
    case 'first_come': return 'policyFirstCome';
    case 'reserved_capacity': return 'policyReservedCapacity';
    case 'staff_placement': return 'policyStaffPlacement';
    default: return 'endOfQueue';
  }
}

/**
 * Must the form ask for a queue position?
 *
 * @param {{walk_in_policy?: unknown}} config
 * @returns {boolean}
 */
export function needsPosition(config) {
  return effectivePolicy(config) === STAFF_PLACEMENT;
}

/**
 * Build the enqueue body, or the refusal that stops the request.
 *
 * `walk_in_policy` is deliberately absent: the field is retired (MP-10), and a
 * body that carried it would be accepted but ignored — a silent mismatch
 * between what the operator chose and what the facility configured.
 *
 * @param {{doctorId?: string, patientId?: string, config?: object,
 *          position?: unknown}} input
 * @returns {{ok: true, body: object} | {ok: false, error: string}}
 */
export function buildEnqueueBody({ doctorId, patientId, config, position } = {}) {
  if (!doctorId) return { ok: false, error: 'doctor_required' };
  if (!patientId) return { ok: false, error: 'patient_required' };

  const body = { doctor_id: doctorId, patient_id: patientId, entry_source: 'walk_in' };
  if (!needsPosition(config)) return { ok: true, body };

  const wanted = Number(position);
  if (position === '' || position === null || position === undefined
      || !Number.isInteger(wanted) || wanted < 1) {
    return { ok: false, error: 'position_required' };
  }
  body.position = wanted;
  return { ok: true, body };
}
