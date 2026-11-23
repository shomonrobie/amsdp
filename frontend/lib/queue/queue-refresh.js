/* QUE-006 / W2 — a refresh that cannot cause a wrong announcement.
 *
 * The queuing service has no outbound event channel, so the page learns about a
 * call by re-reading the queue. Until now that only happened when the operator
 * acted, which meant a second terminal could sit on a stale list while the
 * first terminal called the next patient. This module owns *when* to re-read.
 *
 * The rules exist to protect the announcement, not to poll harder:
 *
 *   - **a hidden tab does not refresh.** A background tab must not announce;
 *     returning to the tab refreshes immediately, and the freshness rule in
 *     `call-announcer.js` decides whether the calls found there are still
 *     worth speaking. A tab that was away for a while therefore catches up on
 *     *state* without shouting old tokens.
 *   - **one refresh at a time.** Interval ticks, focus, visibility and the
 *     browser coming back online may coincide. The second request is
 *     coalesced into one follow-up refresh instead of piling up.
 *   - **a failed refresh is never fatal.** The queue keeps rendering the last
 *     good list; a network error is reported to the page's error surface and
 *     nothing else changes.
 *
 * It knows nothing about queue state, audio or permissions: `refresh` is the
 * page's own loader. Timers and the document are injected so the behaviour can
 * be tested without a browser.
 */

/** 20 seconds: fast enough for a second terminal, quiet enough to be invisible. */
export const DEFAULT_REFRESH_INTERVAL_MS = 20000;

/**
 * @param {object} options
 * @param {(reason: string) => Promise<void>|void} options.refresh
 * @param {object} [options.document] the `document` whose visibility matters
 * @param {object} [options.window] the target for `online` / `focus`
 * @param {number} [options.intervalMs] 0 disables the interval
 * @param {Function} [options.setInterval]
 * @param {Function} [options.clearInterval]
 * @param {(error: unknown) => void} [options.onError]
 */
export function createQueueRefresher(options = {}) {
  const refresh = typeof options.refresh === 'function' ? options.refresh : null;
  const doc = options.document && typeof options.document === 'object' ? options.document : null;
  const win = options.window && typeof options.window === 'object' ? options.window : null;
  const intervalMs = Number.isFinite(options.intervalMs)
    ? Math.max(0, options.intervalMs) : DEFAULT_REFRESH_INTERVAL_MS;
  const setIntervalFn = typeof options.setInterval === 'function'
    ? options.setInterval : (fn, ms) => setInterval(fn, ms);
  const clearIntervalFn = typeof options.clearInterval === 'function'
    ? options.clearInterval : (handle) => clearInterval(handle);
  const onError = typeof options.onError === 'function' ? options.onError : null;

  let started = false;
  let inFlight = false;
  let queued = false;
  let timer = null;

  /** A tab with no usable visibility information is treated as visible. */
  function visible() {
    if (!doc || typeof doc.visibilityState !== 'string') return true;
    return doc.visibilityState === 'visible';
  }

  /**
   * Re-read the queue now.
   * @returns {Promise<{status: string}>} `refreshed`, `hidden`, `coalesced`,
   *   `failed` or `unwired` — never rejects.
   */
  async function run(reason = 'manual') {
    if (!refresh) return { status: 'unwired' };
    if (!visible()) return { status: 'hidden' };
    if (inFlight) { queued = true; return { status: 'coalesced' }; }
    inFlight = true;
    try {
      await refresh(reason);
      return { status: 'refreshed' };
    } catch (error) {
      if (onError) {
        try { onError(error); } catch (err) { /* the error surface must not break the timer */ }
      }
      return { status: 'failed', error };
    } finally {
      inFlight = false;
      if (queued) {
        queued = false;
        // Let the current call settle before the follow-up starts.
        Promise.resolve().then(() => run('queued'));
      }
    }
  }

  function onVisibility() {
    if (visible()) run('visible');
  }
  function onOnline() { run('online'); }
  function onFocus() { run('focus'); }

  function listen(target, type, handler) {
    if (target && typeof target.addEventListener === 'function') {
      target.addEventListener(type, handler);
      return true;
    }
    return false;
  }

  function unlisten(target, type, handler) {
    if (target && typeof target.removeEventListener === 'function') {
      target.removeEventListener(type, handler);
    }
  }

  function start() {
    if (started) return;
    started = true;
    listen(doc, 'visibilitychange', onVisibility);
    listen(win, 'online', onOnline);
    listen(win, 'focus', onFocus);
    if (intervalMs > 0) {
      timer = setIntervalFn(() => { if (visible()) run('interval'); }, intervalMs);
    }
  }

  function stop() {
    if (!started) return;
    started = false;
    unlisten(doc, 'visibilitychange', onVisibility);
    unlisten(win, 'online', onOnline);
    unlisten(win, 'focus', onFocus);
    if (timer !== null) {
      clearIntervalFn(timer);
      timer = null;
    }
  }

  return {
    start,
    stop,
    run,
    /** Test and diagnostics hook: is a refresh currently in flight? */
    isRunning: () => inFlight,
    isStarted: () => started,
  };
}
