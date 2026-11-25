/* QUE-006 / W2 — which queue entries just earned a call announcement.
 *
 * The queuing service has no outbound event channel (no websocket, no SSE), so
 * "announce when a patient is called" is observed on the client that already
 * refreshes the queue. This helper is the decision part of that, kept pure so it
 * can be tested without React:
 *
 *   - only a *transition* counts. An entry that was already `called` when the
 *     page loaded is not re-announced, which is why the first observation seeds
 *     the tracker instead of speaking;
 *   - since MP-08 a recall is `called -> called`, so the status alone can no
 *     longer describe a new call. The server-published `call_event_id` (W2,
 *     `queuing/events.py`) is therefore tracked alongside the status: a *new
 *     event id* is a new call even when the status never changed. An entry with
 *     no published id behaves exactly as before;
 *   - a stale or duplicate response cannot steal an announcement: the delivery
 *     claim only accepts the entry's *current* event id and refuses an older
 *     one with 409, so a reactivated past event never plays;
 *   - an entry that disappears stays out of the next tracker, so a later change
 *     of the same id is still a fresh transition;
 *   - nothing is invented: the entry is returned as it arrived.
 */

/** Separator inside a tracker value. Status names never contain it. */
const SEP = '|';

/** The tracker value for one entry: its status, plus its call event when known. */
function trackerValue(status, eventId) {
  return eventId ? status + SEP + eventId : status;
}

/** Split a tracker value back into its two parts. */
function trackerParts(value) {
  const raw = typeof value === 'string' ? value : '';
  const at = raw.indexOf(SEP);
  if (at === -1) return { status: raw, eventId: '' };
  return { status: raw.slice(0, at), eventId: raw.slice(at + 1) };
}

/**
 * @param {Map<string, string>} previous tracker from the last render
 * @param {Array<{id?: unknown, status?: unknown, call_event_id?: unknown}>} entries current queue
 * @param {{status?: string}} [options]
 * @returns {{next: Map<string, string>, transitioned: Array<object>}}
 */
export function trackCalledTransitions(previous, entries, options = {}) {
  const target = typeof options.status === 'string' ? options.status : 'called';
  const seen = previous instanceof Map ? previous : new Map();
  const next = new Map();
  const transitioned = [];

  (Array.isArray(entries) ? entries : []).forEach((entry) => {
    if (!entry || typeof entry !== 'object' || typeof entry.id !== 'string') return;
    const status = typeof entry.status === 'string' ? entry.status : '';
    const eventId = typeof entry.call_event_id === 'string'
      ? entry.call_event_id.trim() : '';
    const before = seen.get(entry.id);
    next.set(entry.id, trackerValue(status, eventId));
    if (before === undefined) return;             // first observation seeds only
    const was = trackerParts(before);
    const becameTarget = was.status !== target && status === target;
    const newEvent = eventId !== '' && was.eventId !== eventId;
    if (becameTarget || newEvent) transitioned.push(entry);
  });

  return { next, transitioned };
}
