/* QUE-006 / W2 — which queue entries just became `called`.
 *
 * The queuing service has no outbound event channel (no websocket, no SSE), so
 * "announce when a patient is called" is observed on the client that already
 * refreshes the queue. This helper is the decision part of that, kept pure so it
 * can be tested without React:
 *
 *   - only a *transition* counts. An entry that was already `called` when the
 *     page loaded is not re-announced, which is why the first observation seeds
 *     the tracker instead of speaking;
 *   - an entry that disappears stays out of the next tracker, so a later change
 *     of the same id is still a fresh transition;
 *   - nothing is invented: the entry is returned as it arrived.
 */

/**
 * @param {Map<string, string>} previous tracker from the last render
 * @param {Array<{id?: unknown, status?: unknown}>} entries current queue
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
    const before = seen.get(entry.id);
    next.set(entry.id, status);
    if (before !== undefined && before !== target && status === target) {
      transitioned.push(entry);
    }
  });

  return { next, transitioned };
}
