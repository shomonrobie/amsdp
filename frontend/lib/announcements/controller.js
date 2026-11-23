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
import { PLAYBACK } from './prerecorded-audio.js';

export const ACTIVATION = Object.freeze({
  UNKNOWN: 'unknown',   // no gesture yet — the operator has not enabled audio
  GRANTED: 'granted',   // a gesture unlocked playback (or playback already started)
  BLOCKED: 'blocked',   // the browser refused; wait for a fresh gesture
});

/** Spoken during activation only. Silent, and short enough to be inaudible. */
export const PRIME_TEXT = ' ';

const DEFAULT_DEDUPE_WINDOW_MS = 5000;

/**
 * The approved playback vocabulary — D-6, product owner decision 2026-11-22.
 *
 * A sentence that finished is `completed`; a sentence that started and was then
 * stopped is `interrupted`. The other terminal words (`failed`, `blocked`,
 * `busy`, `unavailable`) are unchanged. The pre-merge spellings (`spoken`,
 * `cancelled`, `error`, `unsupported`) are deliberately *not* accepted here: a
 * transport that returns one is reported as `failed(status_<word>)` rather than
 * being silently recorded as a delivered announcement.
 */
const TRANSPORT_STATUS = Object.freeze({
  [OUTCOME.COMPLETED]: OUTCOME.COMPLETED,
  [OUTCOME.INTERRUPTED]: OUTCOME.INTERRUPTED,
  [OUTCOME.FAILED]: OUTCOME.FAILED,
  [OUTCOME.BLOCKED]: OUTCOME.BLOCKED,
  [OUTCOME.BUSY]: OUTCOME.BUSY,
  [OUTCOME.UNAVAILABLE]: OUTCOME.UNAVAILABLE,
});

/**
 * Translate a transport's result into the approved vocabulary.
 *
 * Every transport result passes through here before it becomes `last.status`,
 * the logged outcome or the delivery report, so the controller reports exactly
 * the six words above no matter which engine ran.
 *
 * @param {{status?: string, reason?: string}} result
 */
function normaliseTransport(result) {
  if (!result || typeof result !== 'object') {
    return { status: OUTCOME.FAILED, reason: 'no_transport_outcome' };
  }
  const status = TRANSPORT_STATUS[result.status];
  if (status) return { ...result, status };
  return {
    ...result,
    status: OUTCOME.FAILED,
    reason: result.reason || ('status_' + (result.status || 'unknown')),
  };
}

/**
 * @param {object} options
 * @param {ReturnType<import('./speech-synthesis.js').createSpeechSynthesisAdapter>} options.adapter
 * @param {ReturnType<import('./prerecorded-audio.js').createPrerecordedPlayer>} [options.player]
 *        the prerecorded engine. QUE-006 makes prerecorded playback the primary
 *        mechanism, so it is the default transport whenever a player is given.
 * @param {'prerecorded'|'speech'} [options.strategy] explicit transport choice.
 *        Asking for `prerecorded` without a player is refused rather than
 *        silently downgraded: a substituted mechanism must never be accidental.
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
  const player = options.player && typeof options.player.play === 'function'
    ? options.player : null;
  if (options.strategy === 'prerecorded' && !player) {
    throw new TypeError('strategy "prerecorded" requires a prerecorded player');
  }
  const transport = options.strategy === 'speech' ? 'speech'
    : (player && options.strategy !== 'speech' ? 'prerecorded' : 'speech');

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
    if (transport === 'prerecorded') {
      // A pack reports its own readiness; the browser's voice list is irrelevant
      // to prerecorded playback and must never decide it.
      const cap = typeof player.capability === 'function'
        ? player.capability() : { status: 'no_voice' };
      const status = cap.status === 'ready' ? CAPABILITY.READY
        : (cap.status === 'pending' ? CAPABILITY.PENDING : CAPABILITY.NO_VOICE);
      return { status, voice: null, voices: [] };
    }
    if (!adapter.isSupported()) {
      return { status: CAPABILITY.UNSUPPORTED, voice: null, voices: [] };
    }
    return adapter.capability(language);
  }

  function getState() {
    const cap = capabilityNow();
    const supported = transport === 'prerecorded' ? true : adapter.isSupported();
    const voice = cap.voice || null;
    const playerState = transport === 'prerecorded' && typeof player.getState === 'function'
      ? player.getState() : {};
    return {
      enabled,
      language,
      transport,
      supported,
      capability: cap.status,
      packId: playerState.packId || '',
      packVersion: playerState.version || 0,
      voiceLang: voice ? voice.voiceLang : null,
      voiceName: voice ? voice.name : null,
      voiceFallback: voice ? voice.fallback === true : false,
      activation,
      requiresActivation: supported && enabled && activation !== ACTIVATION.GRANTED,
      speaking: transport === 'prerecorded'
        ? playerState.playing === true
        : (typeof adapter.isSpeaking === 'function' ? adapter.isSpeaking() : false),
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
    if (result.status === OUTCOME.COMPLETED) activation = ACTIVATION.GRANTED;
    else if (result.status === OUTCOME.BLOCKED) activation = ACTIVATION.BLOCKED;
    else if (result.status === OUTCOME.FAILED && result.reason === 'blocked') {
      activation = ACTIVATION.BLOCKED;
    }
  }

  /**
   * Play one announcement through the prerecorded engine.
   *
   * The mapping is the honest one: only the final clip's `ended` becomes
   * `completed`; a playback we stopped becomes `interrupted` (D-6); every other
   * outcome becomes `failed` with its reason. Nothing here can make a
   * half-played sentence look like success.
   */
  async function playPrerecorded(payload) {
    let outcome;
    try {
      outcome = await player.play({ token: payload.token, room: payload.room });
    } catch (err) {
      return { status: OUTCOME.FAILED, reason: 'player_threw' };
    }
    if (!outcome || typeof outcome !== 'object') {
      return { status: OUTCOME.FAILED, reason: 'player_no_outcome' };
    }
    if (outcome.status === PLAYBACK.COMPLETED) {
      return { status: OUTCOME.COMPLETED, transport: 'prerecorded', completed: true };
    }
    if (outcome.status === PLAYBACK.BUSY) return { status: OUTCOME.BUSY };
    if (outcome.status === PLAYBACK.INTERRUPTED) return { status: OUTCOME.INTERRUPTED };
    const failure = {
      status: OUTCOME.FAILED,
      reason: outcome.reason || 'playback_failed',
      transport: 'prerecorded',
    };
    if (Array.isArray(outcome.missing)) failure.missing = outcome.missing;
    return failure;
  }

  /**
   * Unlock audio from an operator gesture ("Enable announcements").
   *
   * Prerecorded playback unlocks by playing the catalogue's silent pause clip;
   * speech playback primes with a silent utterance. Either way the prime is not
   * an announcement, so it never becomes `last`.
   *
   * @returns {Promise<{status: string, reason?: string}>}
   */
  async function activate() {
    if (transport === 'prerecorded') {
      if (typeof player.prime !== 'function') {
        notify();
        return { status: 'unavailable', reason: 'no_prime_support' };
      }
      let primed;
      try {
        primed = await player.prime();
      } catch (err) {
        primed = { status: 'failed', reason: 'player_threw' };
      }
      if (primed && primed.status === 'primed') activation = ACTIVATION.GRANTED;
      else if (primed && primed.status === 'failed' && primed.reason === 'blocked') {
        activation = ACTIVATION.BLOCKED;
      }
      notify();
      return primed;
    }
    if (!adapter.isSupported()) {
      notify();
      return { status: OUTCOME.UNAVAILABLE };
    }
    let result;
    try {
      result = await adapter.speak(PRIME_TEXT, { language, prime: true, volume: 0 });
    } catch (err) {
      result = { status: OUTCOME.FAILED, reason: 'adapter_threw' };
    }
    result = normaliseTransport(result);
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
    if (transport === 'speech' && !adapter.isSupported()) {
      return record({ status: OUTCOME.UNAVAILABLE }, null, input, source, lang);
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
    if (transport === 'prerecorded') {
      result = await playPrerecorded(input);
    } else {
      try {
        result = await adapter.speak(content.text, { language: content.language });
      } catch (err) {
        result = { status: OUTCOME.FAILED, reason: 'adapter_threw' };
      }
      result = normaliseTransport(result);
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
   * Re-read the transport's capability and tell the UI.
   * Used when the voice pack finishes loading after the controller exists.
   */
  function refresh() { notify(); }

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
    cancel: () => {
      if (transport === 'prerecorded' && typeof player.cancel === 'function') player.cancel();
      else if (typeof adapter.cancel === 'function') adapter.cancel();
      notify();
    },
    setLanguage,
    setEnabled,
    refresh,
    dispose,
  };

  return controller;
}
