/* QUE-006 / POD-12 — the queue Call action (closes gap QOP-001).
 *
 * `call` is a *server* action, not a client one. The product already has it:
 * `PATCH /api/v1/queue/{id}` with `{"action": "call"}` moves `waiting -> called`,
 * is authorised by `queue.manage` and is audited as `queue.call`
 * (`backend/queuing/main.py:395-404`). This module adds no endpoint and no
 * second transition — it holds the two decisions the queue page needs, kept
 * pure so they can be tested without React:
 *
 *   - `isCallable()` — which entries the control may offer. The server also
 *     permits `skipped -> called`; the interface deliberately does not offer
 *     that, because a skipped entry is *recovered* (BR §27A), not called.
 *   - `createCallGate()` — a synchronous single-flight guard. React state is
 *     asynchronous, so two clicks in one tick would otherwise send two PATCHes;
 *     the ref-based gate refuses the second before any request exists.
 *
 * `performCall()` is the sequence: authorisation -> eligibility -> gate ->
 * request. It knows nothing about audio. The announcement is driven by the
 * *observed* `waiting -> called` transition after the refetch
 * (`lib/announcements/queue-transitions.js`), so a failed request cannot speak,
 * and playback can never delay or reverse the queue write.
 */

/** The one action string the existing PATCH endpoint accepts. */
export const CALL_ACTION = 'call';

/** The only status the interface offers the control for. */
export const CALLABLE_STATUS = 'waiting';

/**
 * May the Call control be offered for *entry*?
 *
 * Deliberately says nothing about the user: authorisation is a separate
 * argument to `performCall()` and is enforced server-side regardless.
 *
 * @param {{id?: unknown, status?: unknown}} entry
 * @returns {boolean}
 */
export function isCallable(entry) {
  if (!entry || typeof entry !== 'object') return false;
  if (typeof entry.id !== 'string' || entry.id === '') return false;
  return entry.status === CALLABLE_STATUS;
}

/**
 * One in-flight call at a time, decided synchronously.
 *
 * @returns {{begin: Function, end: Function, current: Function}}
 */
export function createCallGate() {
  let inFlight = '';
  return {
    /** Claim the gate for *id*. Returns false when a call is already pending. */
    begin(id) {
      const key = typeof id === 'string' ? id : '';
      if (!key || inFlight) return false;
      inFlight = key;
      return true;
    },
    /** Release the gate — unconditionally when *id* is omitted. */
    end(id) {
      if (inFlight && (id === undefined || id === inFlight)) inFlight = '';
    },
    /** The id currently in flight, or ''. */
    current() {
      return inFlight;
    },
  };
}

/**
 * Run one queue call.
 *
 * @param {object} options
 * @param {object} options.entry the queue entry as rendered
 * @param {boolean} options.authorised the caller's `queue.manage` decision
 * @param {object} options.gate a gate from `createCallGate()`
 * @param {Function} options.request `(id, payload) => Promise` — the page's
 *   `apiFetch` adapter; the payload is always `{action: 'call', reason: ''}`
 * @returns {Promise<{status: string, error?: unknown}>} one of `called`,
 *   `forbidden`, `ineligible`, `busy`, `failed`
 */
export async function performCall({ entry, authorised, gate, request } = {}) {
  if (authorised !== true) return { status: 'forbidden' };
  if (!isCallable(entry)) return { status: 'ineligible' };
  if (typeof request !== 'function') return { status: 'failed', error: new TypeError('request is required') };

  const openGate = gate && typeof gate.begin === 'function' ? gate : createCallGate();
  if (!openGate.begin(entry.id)) return { status: 'busy' };

  try {
    await request(entry.id, { action: CALL_ACTION, reason: '' });
    return { status: 'called' };
  } catch (error) {
    return { status: 'failed', error };
  } finally {
    openGate.end(entry.id);
  }
}
