/* QUE-006 / F3 — the announcement deduplication store.
 *
 * The controller used to remember a single event key and a single timestamp.
 * That is wrong in three separate ways (F3.3):
 *
 *   1. any intervening event forgets the earlier one, so a re-delivery of A
 *      after B is announced again *inside* the window meant to suppress it;
 *   2. the key was consumed **before** the attempt, so a refusal
 *      (`needs_activation`) or a failure left the event marked as announced and
 *      the patient was never called;
 *   3. the slot recorded that a key had been *seen*, not what had happened to
 *      it, so retry, exhaustion and operator-visible failure had no
 *      representation.
 *
 * This module replaces the slot with one record per event key whose `state` is
 * the only source of truth for "was it announced?".
 *
 * Deliberate constraints:
 *
 *   - **No timers.** Expiry is evaluated on read and swept on write; a
 *     background timer would keep a kiosk page awake for a whole shift.
 *   - **The clock is injected**, so every test is deterministic.
 *   - **Bounded memory** (`maxKeys`, default 512). Eviction is deterministic and
 *     never evicts an in-flight attempt.
 *   - **No spoken text is stored.** A record carries the event key, a state and
 *     a normalised reason — never the sentence, never a patient.
 *
 * Storage is per browser tab by design; cross-client suppression needs the
 * server-side event contract (ANN-002/ANN-005) and is out of scope here.
 */

/** The states a record can be in. `state` decides suppression, nothing else. */
export const DEDUPE_STATE = Object.freeze({
  ATTEMPTING: 'attempting',
  COMPLETED: 'completed',
  FAILED: 'failed',
  INTERRUPTED: 'interrupted',
  BLOCKED: 'blocked',
  EXHAUSTED: 'exhausted',
});

/** Defaults per the §F3.4 policy table. The TTLs are an engineering
 *  recommendation and require owner ratification (§18 O-5). */
export const DEDUPE_DEFAULTS = Object.freeze({
  //: A completed event is suppressed for ten minutes: a re-delivery can arrive
  //: after a page refresh or a reconnect, and a genuine recall is a new key.
  completedTtlMs: 10 * 60 * 1000,
  //: A failed attempt is retryable, so it must not hold the key for long.
  failureTtlMs: 60 * 1000,
  //: A blocked browser is not re-attempted on events, only on a gesture.
  blockedTtlMs: 10 * 60 * 1000,
  maxAttempts: 3,
  maxKeys: 512,
  baseRetryMs: 5000,
  maxRetryMs: 30000,
});

/** `min(5000 * 2 ** (attempts - 1), 30000)` — never a tight retry loop. */
export function retryDelayMs(attempts, options = {}) {
  const base = Number.isFinite(options.baseRetryMs) ? options.baseRetryMs : DEDUPE_DEFAULTS.baseRetryMs;
  const max = Number.isFinite(options.maxRetryMs) ? options.maxRetryMs : DEDUPE_DEFAULTS.maxRetryMs;
  const n = Math.max(1, Number(attempts) || 1);
  return Math.min(base * (2 ** (n - 1)), max);
}

function positive(value, fallback) {
  return Number.isFinite(value) && value >= 0 ? value : fallback;
}

/**
 * @param {object} [options]
 * @param {() => number} [options.now] injected clock (mandatory in tests)
 */
export function createAnnouncementStore(options = {}) {
  const now = typeof options.now === 'function' ? options.now : () => Date.now();
  const completedTtlMs = positive(options.completedTtlMs, DEDUPE_DEFAULTS.completedTtlMs);
  const failureTtlMs = positive(options.failureTtlMs, DEDUPE_DEFAULTS.failureTtlMs);
  const blockedTtlMs = positive(options.blockedTtlMs, DEDUPE_DEFAULTS.blockedTtlMs);
  const maxAttempts = Math.max(1, Number.isFinite(options.maxAttempts)
    ? options.maxAttempts : DEDUPE_DEFAULTS.maxAttempts);
  const maxKeys = Math.max(1, Number.isFinite(options.maxKeys) ? options.maxKeys : DEDUPE_DEFAULTS.maxKeys);
  const retryOptions = {
    baseRetryMs: positive(options.baseRetryMs, DEDUPE_DEFAULTS.baseRetryMs),
    maxRetryMs: positive(options.maxRetryMs, DEDUPE_DEFAULTS.maxRetryMs),
  };

  /** @type {Map<string, {key: string, state: string, attempts: number,
   *   firstAttemptAt: number, lastAttemptAt: number, completedAt: number|null,
   *   expiresAt: number, lastReason: string}>} */
  const records = new Map();

  function isExpired(record, at) {
    // `null` means "no expiry of its own" (an in-flight attempt). A numeric
    // expiry must not be confused with a zero-valued injected clock.
    return record.expiresAt !== null && at >= record.expiresAt;
  }

  /** Read: an expired record is no longer a record. Never a timer. */
  function get(key) {
    if (!key) return null;
    const record = records.get(key);
    if (!record) return null;
    if (isExpired(record, now())) {
      records.delete(key);
      return null;
    }
    return { ...record };
  }

  /** Drop expired records. Called on every write; O(size) on a bounded map. */
  function sweep(at) {
    records.forEach((record, key) => {
      if (isExpired(record, at)) records.delete(key);
    });
  }

  /**
   * Deterministic eviction: `completed` first (earliest expiry), then the
   * oldest `lastAttemptAt`. `attempting` is never evicted — dropping an
   * in-flight record would let the same event be announced twice.
   */
  function evict() {
    if (records.size <= maxKeys) return;
    const candidates = Array.from(records.values()).filter(
      (r) => r.state !== DEDUPE_STATE.ATTEMPTING);
    candidates.sort((a, b) => {
      const aDone = a.state === DEDUPE_STATE.COMPLETED ? 0 : 1;
      const bDone = b.state === DEDUPE_STATE.COMPLETED ? 0 : 1;
      if (aDone !== bDone) return aDone - bDone;
      if (aDone === 0 && a.expiresAt !== b.expiresAt) return a.expiresAt - b.expiresAt;
      return a.lastAttemptAt - b.lastAttemptAt;
    });
    let overflow = records.size - maxKeys;
    for (const victim of candidates) {
      if (overflow <= 0) break;
      records.delete(victim.key);
      overflow -= 1;
    }
  }

  function ensureCapacity(at) {
    sweep(at);
    evict();
  }


  /**
   * May this event be announced now?
   *
   * @param {string} key
   * @param {{activationGranted?: boolean, userGesture?: boolean}} [context]
   * @returns {{suppress: boolean, status: string, reason: string}}
   *   `status` is the controller's outcome vocabulary for a suppressed attempt:
   *   `duplicate`, `busy`, `exhausted`, `retry_wait` or `needs_activation`.
   */
  function shouldSuppress(key, context = {}) {
    const record = get(key);
    if (!record) return { suppress: false, status: '', reason: '' };
    const at = now();
    switch (record.state) {
      case DEDUPE_STATE.ATTEMPTING:
        // The in-flight attempt owns the outcome; never overlap it.
        return { suppress: true, status: 'busy', reason: 'in_flight' };
      case DEDUPE_STATE.COMPLETED:
        return { suppress: true, status: 'duplicate', reason: 'already_completed' };
      case DEDUPE_STATE.EXHAUSTED:
        return { suppress: true, status: 'exhausted', reason: 'max_attempts' };
      case DEDUPE_STATE.BLOCKED:
        // A fresh operator gesture may retry; nothing else may.
        if (context.userGesture === true) return { suppress: false, status: '', reason: '' };
        return { suppress: true, status: 'needs_activation', reason: 'activation_blocked' };
      case DEDUPE_STATE.FAILED:
      case DEDUPE_STATE.INTERRUPTED: {
        // Bounded retry: a failure is never permanently "announced".
        const wait = retryDelayMs(record.attempts, retryOptions);
        if (at - record.lastAttemptAt < wait) {
          return { suppress: true, status: 'retry_wait', reason: 'retry_backoff' };
        }
        return { suppress: false, status: '', reason: '' };
      }
      default:
        return { suppress: false, status: '', reason: '' };
    }
  }

  /** Reserve the key for an attempt that is about to start. */
  function begin(key, reason = '') {
    if (!key) return null;
    const at = now();
    ensureCapacity(at);
    const previous = get(key);
    const record = {
      key,
      state: DEDUPE_STATE.ATTEMPTING,
      attempts: previous ? previous.attempts : 0,
      firstAttemptAt: previous ? previous.firstAttemptAt : at,
      lastAttemptAt: at,
      completedAt: previous ? previous.completedAt : null,
      // An in-flight attempt has no expiry of its own: its watchdog belongs to
      // the renderer, and a stale `attempting` record would suppress forever.
      expiresAt: null,
      lastReason: reason,
    };
    records.set(key, record);
    return { ...record };
  }

  /**
   * Record what actually happened. This is the only writer of a terminal state,
   * and it is only ever called with a *terminal* outcome (F2): a renderer that
   * resolved at `start` would mark an unheard event completed.
   *
   * @param {string} key
   * @param {{status: string, reason?: string}} outcome
   */
  function settle(key, outcome = {}) {
    if (!key) return null;
    const at = now();
    ensureCapacity(at);
    const previous = get(key);
    const status = outcome.status;
    const reason = outcome.reason || '';
    const counted = status === DEDUPE_STATE.COMPLETED
      || status === DEDUPE_STATE.FAILED
      || status === DEDUPE_STATE.INTERRUPTED
      || status === DEDUPE_STATE.BLOCKED;
    if (!counted) {
      // `busy` / `unavailable` / `skipped` are not attempts: the event stays
      // announcable, and no expiry is set (F3.4 "cancelled" rule).
      if (previous) records.delete(key);
      return null;
    }
    const attempts = (previous ? previous.attempts : 0) + 1;
    const exhausted = attempts >= maxAttempts
      && (status === DEDUPE_STATE.FAILED || status === DEDUPE_STATE.INTERRUPTED);
    const state = exhausted ? DEDUPE_STATE.EXHAUSTED : status;
    const ttl = state === DEDUPE_STATE.COMPLETED ? completedTtlMs
      : state === DEDUPE_STATE.BLOCKED ? blockedTtlMs
        : failureTtlMs;
    const record = {
      key,
      state,
      attempts,
      firstAttemptAt: previous ? previous.firstAttemptAt : at,
      lastAttemptAt: at,
      completedAt: state === DEDUPE_STATE.COMPLETED ? at
        : (previous ? previous.completedAt : null),
      expiresAt: at + ttl,
      lastReason: reason,
    };
    records.set(key, record);
    return { ...record };
  }

  /** Release a key that was never heard and must not be remembered as an attempt. */
  function release(key) {
    if (key) records.delete(key);
  }

  function size() {
    return records.size;
  }

  function keys() {
    return Array.from(records.keys());
  }

  function reset() {
    records.clear();
  }

  return { get, shouldSuppress, begin, settle, release, size, keys, reset, maxKeys, maxAttempts };
}
