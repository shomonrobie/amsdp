/* QUE-006 / W2 — the announcement delivery protocol (POD-4, V-12).
 *
 * Three decisions live here, kept pure so they can be tested without a browser:
 *
 *   1. **Identity.** A call event's identity is the server's
 *      (`entry.call_event_id`, derived from `status_history`). The browser never
 *      invents one; an entry without an id is never announced. That is what
 *      makes a recall a *new* event and a repeated response the *same* event.
 *   2. **The claim.** The first terminal to POST the event wins the delivery
 *      slot; every other terminal is told `claimed: false` and stays silent.
 *      Duplicate protection is therefore durable across browsers, not a
 *      5 second window in one tab.
 *   3. **The outcome.** What the browser reports is what it can observe. Only
 *      the final clip's `ended` makes `completed`; a started but unconfirmed
 *      announcement is `failed`, never a guess.
 *
 * Nothing in this file fetches, plays, or keeps state.
 */

/** Mirrors `OUTCOMES` in `backend/queuing/announcements.py`. */
export const DELIVERY_OUTCOME = Object.freeze({
  COMPLETED: 'completed',            // the final clip reported `ended`
  FAILED: 'failed',                  // playback failed, or could not be confirmed
  BLOCKED: 'blocked',                // the browser refused playback
  INTERRUPTED: 'interrupted',        // started, then cancelled by page or browser
  SKIPPED_BUSY: 'skipped_busy',      // claimed, but a newer call took precedence
  SKIPPED_DUPLICATE: 'skipped_duplicate', // suppressed as a duplicate of this event
});

/** The outcomes a client may report, in the order the server documents them. */
export const OUTCOME_VALUES = Object.freeze([
  DELIVERY_OUTCOME.COMPLETED,
  DELIVERY_OUTCOME.FAILED,
  DELIVERY_OUTCOME.BLOCKED,
  DELIVERY_OUTCOME.INTERRUPTED,
  DELIVERY_OUTCOME.SKIPPED_BUSY,
  DELIVERY_OUTCOME.SKIPPED_DUPLICATE,
]);

/** Server limits: `call_event_id` and `reason` are clipped to 120 characters. */
export const MAX_EVENT_ID_LENGTH = 120;
export const MAX_REASON_LENGTH = 120;

/**
 * How old a call event may be for an *automatic* announcement.
 *
 * A tab that was hidden, offline or asleep may return to a list containing a
 * call that happened long ago. Announcing it would be a fresh, wrong
 * instruction in the waiting room, so an automatic announcement only speaks a
 * call from this window. The operator's explicit "Announce" button is not
 * bounded: a deliberate repeat is a decision, not a notification.
 */
export const DEFAULT_MAX_EVENT_AGE_MS = 120000;

/** Tolerance for a server timestamp a few seconds ahead of the browser clock. */
const CLOCK_SKEW_MS = 5000;

function clip(value, limit) {
  const text = typeof value === 'string' ? value : '';
  return text.length > limit ? text.slice(0, limit) : text;
}

/**
 * The server event id of an entry, or `''`.
 * @param {{call_event_id?: unknown}} entry
 */
export function eventIdOf(entry) {
  if (!entry || typeof entry !== 'object') return '';
  const value = entry.call_event_id;
  if (typeof value !== 'string') return '';
  const id = value.trim();
  return id.length > MAX_EVENT_ID_LENGTH ? id.slice(0, MAX_EVENT_ID_LENGTH) : id;
}

/** `POST /api/v1/queue/{entry_id}/announcement` */
export function deliveryPath(entryId) {
  return `/api/v1/queue/${encodeURIComponent(String(entryId))}/announcement`;
}

/** `POST /api/v1/queue/announcements/{delivery_id}/outcome` */
export function outcomePath(deliveryId) {
  return `/api/v1/queue/announcements/${encodeURIComponent(String(deliveryId))}/outcome`;
}

/**
 * The claim request for one entry: path and body.
 *
 * The body carries the voice selection that was actually used, so the persisted
 * record answers "which pack announced this?" — the fact POD-4 asks for. Scope
 * is never sent: the server derives organisation, branch and actor.
 *
 * @param {{id?: unknown, call_event_id?: unknown}} entry
 * @param {{language?: string, voicePackId?: string, voicePackVersion?: number,
 *          transport?: string}} [descriptor] the controller's current state
 * @returns {{path: string, body: object}|null} null when there is no event id
 */
export function claimRequest(entry, descriptor = {}) {
  const eventId = eventIdOf(entry);
  if (!eventId) return null;
  const entryId = entry && typeof entry.id === 'string' ? entry.id : '';
  if (!entryId) return null;
  const version = Number(descriptor.voicePackVersion);
  return {
    path: deliveryPath(entryId),
    body: {
      event_id: eventId,
      language: descriptor.language === 'en' ? 'en' : 'bn',
      voice_pack_id: typeof descriptor.voicePackId === 'string' ? descriptor.voicePackId : '',
      voice_pack_version: Number.isFinite(version) && version > 0 ? Math.trunc(version) : 0,
      transport: descriptor.transport === 'speech' ? 'speech' : 'prerecorded',
    },
  };
}

/**
 * The outcome request for a claimed delivery, or `null` when the outcome is not
 * one the server accepts (never send an unknown status).
 *
 * @param {string} deliveryId
 * @param {string} outcome one of `OUTCOME_VALUES`
 * @param {string} [reason]
 */
export function outcomeRequest(deliveryId, outcome, reason = '') {
  const id = typeof deliveryId === 'string' ? deliveryId.trim() : '';
  if (!id) return null;
  if (!OUTCOME_VALUES.includes(outcome)) return null;
  return { path: outcomePath(id), body: { outcome, reason: clip(reason, MAX_REASON_LENGTH) } };
}

/**
 * May this entry be announced automatically?
 *
 * False when the server timestamp is missing or unparseable: an unknown age is
 * treated as stale, because the alternative is a wrong instruction being spoken
 * in a waiting room.
 *
 * @param {{call_event_at?: unknown}} entry
 * @param {{now?: number, maxAgeMs?: number}} [options]
 */
export function isFreshCallEvent(entry, options = {}) {
  if (!entry || typeof entry !== 'object') return false;
  const raw = entry.call_event_at;
  if (typeof raw !== 'string' || raw === '') return false;
  const at = Date.parse(raw);
  if (!Number.isFinite(at)) return false;
  const now = Number.isFinite(options.now) ? options.now : Date.now();
  const maxAgeMs = Number.isFinite(options.maxAgeMs) && options.maxAgeMs >= 0
    ? options.maxAgeMs : DEFAULT_MAX_EVENT_AGE_MS;
  const age = now - at;
  return age >= -CLOCK_SKEW_MS && age <= maxAgeMs;
}

/**
 * Translate one controller result into the outcome the server records.
 *
 * `completed` is only produced by a *confirmed* completion (`completed: true`,
 * set when the prerecorded engine saw the final clip's `ended`). A speech
 * transport that merely started is `failed`/`completion_unconfirmed`: the
 * browser never told us the sentence finished.
 *
 * @param {{status?: string, reason?: string, completed?: boolean}} result
 * @returns {{outcome: string, reason: string}}
 */
export function classifyAnnouncement(result) {
  const status = result && typeof result.status === 'string' ? result.status : '';
  const reason = result && typeof result.reason === 'string' ? result.reason : '';
  const settle = (outcome, why = reason) => ({ outcome, reason: clip(why, MAX_REASON_LENGTH) });

  switch (status) {
    // D-6 (product owner, 2026-11-22): the playback vocabulary is `completed`
    // / `interrupted`, and the controller normalises every transport result into
    // it before the outcome reaches this classifier. The pre-merge spellings
    // (`spoken`, `cancelled`) are no longer accepted: an unknown status falls to
    // `default` and is recorded honestly as a failure instead of being guessed.
    case 'completed':
      return result && result.completed === true
        ? settle(DELIVERY_OUTCOME.COMPLETED, '')
        : settle(DELIVERY_OUTCOME.FAILED, 'completion_unconfirmed');
    case 'blocked':
      return settle(DELIVERY_OUTCOME.BLOCKED);
    case 'busy':
      return settle(DELIVERY_OUTCOME.SKIPPED_BUSY);
    case 'interrupted':
      return settle(DELIVERY_OUTCOME.INTERRUPTED);
    case 'duplicate':
      return settle(DELIVERY_OUTCOME.SKIPPED_DUPLICATE);
    case 'needs_activation':
      return settle(DELIVERY_OUTCOME.BLOCKED, reason || 'needs_activation');
    case 'disabled':
      return settle(DELIVERY_OUTCOME.BLOCKED, 'disabled');
    case 'skipped':
      // Content was refused (for example a nameless token): nothing was played.
      return settle(DELIVERY_OUTCOME.FAILED, 'content_' + (reason || 'refused'));
    case 'failed':
      return settle(reason === 'blocked'
        ? DELIVERY_OUTCOME.BLOCKED : DELIVERY_OUTCOME.FAILED);
    default:
      return settle(DELIVERY_OUTCOME.FAILED, reason || ('status_' + (status || 'unknown')));
  }
}
