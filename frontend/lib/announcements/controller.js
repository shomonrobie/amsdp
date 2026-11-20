/* QUE-006 / OD-1 — announcement controller.
 *
 * Sits between the browser adapter and the UI. It owns the decisions that must
 * be identical everywhere an announcement is triggered:
 *
 *   - the facility switch (disabled ⇒ nothing is attempted);
 *   - duplicate suppression (the same queue event never speaks twice);
 *   - overlap suppression (one announcement at a time, reported as `busy`);
 *   - user-activation state (a browser that blocked audio is not re-attempted
 *     on every event — only on a fresh operator gesture);
 *   - the observable outcome of the last attempt.
 *
 * It is framework-free so it can be unit-tested; the React shell in
 * `components/queue/QueueAnnouncements.js` only renders its state.
 *
 * Deliberately NOT here (separate requirements, see the implementation report):
 * server-side queue events, facility configuration storage (OD-2), server-side
 * announcement audit, and cross-client ordering.
 */
import { announcementEventKey, buildAnnouncement } from './content.js';
import { CAPABILITY, OUTCOME } from './speech-synthesis.js';

export const ACTIVATION = Object.freeze({
  UNKNOWN: 'unknown',   // no gesture yet — the operator has not enabled audio
  GRANTED: 'granted',   // a gesture unlocked playback (or playback already started)
  BLOCKED: 'blocked',   // the browser refused; wait for a fresh gesture
});

/** Spoken during activation only. Silent, and short enough to be inaudible. */
export const PRIME_TEXT = ' ';

const DEFAULT_DEDUPE_WINDOW_MS = 5000;

/**
 * @param {object} options
 * @param {ReturnType<import('./speech-synthesis.js').createSpeechSynthesisAdapter>} options.adapter
 * @param {'bn'|'en'} [options.language]
 * @param {boolean} [options.enabled]
 * @param {number} [options.dedupeWindowMs]
 * @param {() => number} [options.now]
 * @param {(entry: object) => void|object} [options.logger]
 */
export function createAnnouncementController(options = {}) {
  const adapter = options.adapter;
  if (!adapter || typeof adapter.speak !== 'function') {
    throw new TypeError('createAnnouncementController requires a speech adapter');
  }

  const now = typeof options.now === 'function' ? options.now : () => Date.now();
  const dedupeWindowMs = Number.isFinite(options.dedupeWindowMs)
    ? Math.max(0, options.dedupeWindowMs)
    : DEFAULT_DEDUPE_WINDOW_MS;
  const logger = typeof options.logger === 'function' ? options.logger
    : (options.logger && typeof options.logger.info === 'function' ? options.logger : null);

  let language = options.language === 'en' ? 'en' : 'bn';
  let enabled = options.enabled !== false;
  let activation = ACTIVATION.UNKNOWN;
  /** @type {null|{key: string|null, source: string, status: string, reason: string,
   *               language: string, text: string, at: number}} */
  let last = null;
  let lastEventKey = null;
  let lastEventAt = 0;
  let unsubscribeVoices = null;
  let disposed = false;
  const listeners = new Set();

  function capabilityNow() {
    if (!adapter.isSupported()) {
      return { status: CAPABILITY.UNSUPPORTED, voice: null, voices: [] };
    }
    return adapter.capability(language);
  }

  function getState() {
    const cap = capabilityNow();
    const supported = adapter.isSupported();
    const voice = cap.voice || null;
    return {
      enabled,
      language,
      supported,
      capability: cap.status,
      voiceLang: voice ? voice.voiceLang : null,
      voiceName: voice ? voice.name : null,
      voiceFallback: voice ? voice.fallback === true : false,
      activation,
      requiresActivation: supported && enabled && activation !== ACTIVATION.GRANTED,
      speaking: typeof adapter.isSpeaking === 'function' ? adapter.isSpeaking() : false,
      dedupeWindowMs,
      last: last ? { ...last } : null,
    };
  }

  function notify() {
    if (disposed) return;
    const state = getState();
    Array.from(listeners).forEach((listener) => {
      try { listener(state); } catch (err) { /* a view must not break audio */ }
    });
  }

  /** Announcement outcomes are observable without ever carrying patient data. */
  function log(entry) {
    if (!logger) return;
    const line = {
      event: 'queue.announcement',
      queueEntryId: entry.key || null,
      outcome: entry.status,
      language: entry.language,
      reason: entry.reason || '',
    };
    try {
      if (typeof logger === 'function') logger(line);
      else logger.info('queue.announcement', line);
    } catch (err) { /* logging must never break an announcement */ }
  }

  function record(result, content, payload, source, lang) {
    last = {
      key: announcementEventKey(payload || {}),
      source,
      status: result.status,
      reason: result.reason || '',
      language: content ? content.language : lang,
      text: content ? content.text : '',
      at: now(),
    };
    log(last);
    notify();
    return result;
  }

  function appliesActivation(result) {
    if (result.status === OUTCOME.SPOKEN) activation = ACTIVATION.GRANTED;
    else if (result.status === OUTCOME.BLOCKED) activation = ACTIVATION.BLOCKED;
  }

  /**
   * Unlock audio from an operator gesture ("Enable announcements").
   *
   * The prime utterance is deliberately silent and language-independent: its
   * only job is to prove the browser accepts playback. It is not an
   * announcement, so it never becomes `last`.
   *
   * @returns {Promise<{status: string, reason?: string}>}
   */
  async function activate() {
    if (!adapter.isSupported()) {
      notify();
      return { status: OUTCOME.UNSUPPORTED };
    }
    let result;
    try {
      result = await adapter.speak(PRIME_TEXT, { language, prime: true, volume: 0 });
    } catch (err) {
      result = { status: OUTCOME.ERROR, reason: 'adapter_threw' };
    }
    appliesActivation(result);
    notify();
    return result;
  }

  /**
   * Announce one queue entry.
   *
   * @param {{token?: unknown, doctorName?: unknown, room?: unknown,
   *          queueEntryId?: unknown, eventId?: unknown,
   *          action?: unknown, revision?: unknown}} payload
   * @param {{language?: 'bn'|'en', source?: 'event'|'operator',
   *          userGesture?: boolean}} [opts]
   *        `source: 'operator'` marks a deliberate repeat and bypasses duplicate
   *        suppression. `userGesture: true` marks a call made from a click, which
   *        may recover audio the browser blocked earlier.
   * @returns {Promise<{status: string, reason?: string}>}
   */
  async function announce(payload = {}, opts = {}) {
    const source = opts.source === 'operator' ? 'operator' : 'event';
    const userGesture = opts.userGesture === true;
    const lang = opts.language === 'en' ? 'en' : (opts.language === 'bn' ? 'bn' : language);
    const input = payload && typeof payload === 'object' ? payload : {};

    if (!enabled) return record({ status: 'disabled' }, null, input, source, lang);
    if (!adapter.isSupported()) {
      return record({ status: OUTCOME.UNSUPPORTED }, null, input, source, lang);
    }

    const content = buildAnnouncement(input, lang);
    if (!content.ok) {
      // Refused content is an explicit outcome, never silence and never a throw.
      return record({ status: 'skipped', reason: content.reason }, null, input, source, lang);
    }

    const key = announcementEventKey(input);
    if (source === 'event' && key) {
      const at = now();
      if (lastEventKey === key && (at - lastEventAt) < dedupeWindowMs) {
        return record({ status: 'duplicate' }, content, input, source, lang);
      }
      lastEventKey = key;
      lastEventAt = at;
    }

    if (activation === ACTIVATION.BLOCKED && !userGesture) {
      // Do not hammer a browser that has already refused playback.
      return record({ status: 'needs_activation' }, content, input, source, lang);
    }

    let result;
    try {
      result = await adapter.speak(content.text, { language: content.language });
    } catch (err) {
      result = { status: OUTCOME.ERROR, reason: 'adapter_threw' };
    }
    appliesActivation(result);
    return record(result, content, input, source, lang);
  }

  function setLanguage(value) {
    const next = value === 'en' ? 'en' : 'bn';
    if (next === language) return;
    language = next;
    notify();
  }

  function setEnabled(value) {
    const next = value !== false;
    if (next === enabled) return;
    enabled = next;
    notify();
  }

  /**
   * Start observing the browser's voice list. Returns an unsubscribe function.
   * Safe to call more than once; the previous subscription is replaced.
   */
  function start() {
    if (disposed) return () => {};
    if (unsubscribeVoices) unsubscribeVoices();
    unsubscribeVoices = typeof adapter.subscribeVoices === 'function'
      ? adapter.subscribeVoices(() => notify())
      : null;
    notify();
    return stop;
  }

  function stop() {
    if (unsubscribeVoices) {
      unsubscribeVoices();
      unsubscribeVoices = null;
    }
  }

  /**
   * Subscribe to state changes.
   * @param {(state: object) => void} listener
   * @returns {() => void} unsubscribe
   */
  function subscribe(listener) {
    if (typeof listener !== 'function') return () => {};
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  }

  /** Stop observing and refuse further use. Speech itself is stopped by the adapter owner. */
  function dispose() {
    stop();
    listeners.clear();
    disposed = true;
  }

  const controller = {
    getState,
    subscribe,
    start,
    stop,
    activate,
    announce,
    cancel: () => { if (typeof adapter.cancel === 'function') adapter.cancel(); notify(); },
    setLanguage,
    setEnabled,
    dispose,
  };

  return controller;
}
