/* QUE-006 / W2 — claim, play, report (V-11, V-12, POD-4).
 *
 * The queue page observes a `waiting -> called` transition and hands the entry
 * to this module. The sequence is fixed:
 *
 *   1. **identity** — the server's `call_event_id`, never a local key;
 *   2. **claim** — `POST /api/v1/queue/{id}/announcement`. The first terminal to
 *      claim speaks; every other terminal is told `claimed: false` and stops
 *      here. Two browsers can no longer announce the same call;
 *   3. **play** — only the owner plays, through the existing controller;
 *   4. **report** — the observable outcome is posted back so the server holds a
 *      durable record (POD-4). Reporting can fail without affecting anything the
 *      patient hears, and it never touches queue state.
 *
 * Two rules keep this from becoming a new source of wrong announcements:
 *
 *   - an entry with no `call_event_id` is *never* announced. Historical rows,
 *     rows from an older backend and hand-made payloads all fall out here;
 *   - an automatic announcement must be *fresh* (`isFreshCallEvent`), so a tab
 *     that reconnects after a long pause does not call someone who was called
 *     ten minutes ago. The operator's own "Announce" button is not bounded.
 *
 * `announceCall` never throws and never rejects: the queue transaction has
 * already committed, so a claim, playback or audit failure may only be reported
 * as an outcome — it may never reach the page as an error.
 */
import {
  claimRequest,
  classifyAnnouncement,
  eventIdOf,
  isFreshCallEvent,
  outcomeRequest,
  DEFAULT_MAX_EVENT_AGE_MS,
} from './delivery.js';

/**
 * @param {object} options
 * @param {(payload: object, opts: object) => Promise<object>} options.announce
 *        the controller's `announce` (plays; resolves with its outcome)
 * @param {() => {enabled?: boolean, language?: string, voicePackId?: string,
 *                voicePackVersion?: number, transport?: string}} options.describe
 *        the controller's current state, read at claim time
 * @param {(path: string, body: object) => Promise<object>} options.post
 *        an authenticated POST adapter (the page's `apiFetch`)
 * @param {() => number} [options.now]
 * @param {number} [options.maxEventAgeMs]
 * @param {(record: object) => void} [options.onRecord] observability only
 */
export function createCallAnnouncer(options = {}) {
  const announce = typeof options.announce === 'function' ? options.announce : null;
  const describe = typeof options.describe === 'function' ? options.describe : () => ({});
  const post = typeof options.post === 'function' ? options.post : null;
  const now = typeof options.now === 'function' ? options.now : () => Date.now();
  const maxEventAgeMs = Number.isFinite(options.maxEventAgeMs)
    ? options.maxEventAgeMs : DEFAULT_MAX_EVENT_AGE_MS;
  const onRecord = typeof options.onRecord === 'function' ? options.onRecord : null;

  /** eventId -> 'claiming' | 'owned' | 'foreign' | 'stale' | 'settled' */
  const seen = new Map();

  function record(entry) {
    if (!onRecord) return;
    try { onRecord(entry); } catch (err) { /* observability must not break audio */ }
  }

  function skip(reason, eventId = '') {
    record({ event: 'queue.announcement.skip', eventId, reason });
    return { status: 'skipped', reason, eventId };
  }

  function announceCall(entry, opts = {}) {
    return run(entry, opts).catch((error) => ({
      status: 'error',
      reason: (error && error.message) || 'announcer_threw',
    }));
  }

  async function run(entry, opts) {
    const eventId = eventIdOf(entry);
    if (!eventId) return skip('no_event_id');

    // An announcement is automatic unless it is the operator's own repeat. The
    // flag can be set explicitly; otherwise `source` decides, exactly as the
    // controller decides whether its duplicate window applies.
    const automatic = typeof opts.automatic === 'boolean'
      ? opts.automatic : opts.source !== 'operator';
    // Tab-local guard: the secondary protection. The server claim is primary,
    // but this stops two renders of the same transition from opening two claims.
    // An operator repeat is deliberate, so it is not blocked here — the claim
    // still decides which terminal speaks.
    if (automatic && seen.has(eventId)) return skip('duplicate_local', eventId);
    if (!announce || !post) return skip('not_wired', eventId);

    const state = describe() || {};
    // A disabled facility is not an attempted announcement: no claim is made and
    // no delivery row is created, so the record stays honest.
    if (state.enabled === false) return skip('disabled', eventId);

    if (automatic && !isFreshCallEvent(entry, { now: now(), maxAgeMs: maxEventAgeMs })) {
      seen.set(eventId, 'stale');
      return skip('stale_event', eventId);
    }

    const request = claimRequest(entry, state);
    if (!request) return skip('no_event_id');

    seen.set(eventId, 'claiming');
    let claim;
    try {
      claim = await post(request.path, request.body);
    } catch (error) {
      const status = error && typeof error.status === 'number' ? error.status : 0;
      if (status === 404 || status === 409 || status === 422) {
        // The server refused a definite answer: not our entry, not the current
        // call, or not a callable entry. Nothing is played and nothing is owed.
        seen.set(eventId, 'foreign');
        return skip('claim_rejected', eventId);
      }
      seen.delete(eventId);
      record({ event: 'queue.announcement.claim_failed', eventId,
        reason: (error && error.message) || 'claim_failed' });
      return { status: 'failed', reason: 'claim_failed', eventId };
    }

    if (!claim || claim.claimed !== true) {
      // Another terminal owns this call event; it alone plays and settles the row.
      seen.set(eventId, 'foreign');
      return skip((claim && claim.reason) || 'not_owner', eventId);
    }

    seen.set(eventId, 'owned');
    const deliveryId = typeof claim.delivery_id === 'string' ? claim.delivery_id : '';

    let played;
    try {
      played = await announce({
        queueEntryId: entry.id,
        action: 'call',
        // The controller keys duplicate suppression on this, so the suppression
        // key is now the server's identity rather than a local guess.
        eventId,
        token: entry.token,
        room: entry.room,
      }, {
        source: opts.source === 'operator' ? 'operator' : 'event',
        userGesture: opts.userGesture === true,
      });
    } catch (error) {
      played = { status: 'failed', reason: 'announce_threw' };
    }

    const settled = classifyAnnouncement(played);
    seen.set(eventId, 'settled');

    if (deliveryId) {
      const report = outcomeRequest(deliveryId, settled.outcome, settled.reason);
      if (report) {
        try {
          await post(report.path, report.body);
        } catch (error) {
          // The patient already heard (or did not hear) it; a lost audit report
          // is logged, never retried into the queue path and never thrown.
          record({ event: 'queue.announcement.report_failed', eventId,
            reason: (error && error.message) || 'report_failed' });
        }
      }
    }

    record({ event: 'queue.announcement.settled', eventId, deliveryId,
      outcome: settled.outcome });
    return { status: 'announced', outcome: settled.outcome, eventId, deliveryId };
  }

  return {
    announceCall,
    /** The state this tab holds for one event, or '' when it has none. */
    stateOf: (eventId) => seen.get(eventId) || '',
    reset: () => { seen.clear(); },
  };
}
