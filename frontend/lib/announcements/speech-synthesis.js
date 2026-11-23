/* QUE-006 / OD-1 — browser speech-synthesis adapter.
 *
 * The product owner's OD-1 decision is that queue announcements are spoken
 * **in the browser** by the Web Speech API (`window.speechSynthesis`): no
 * server-side TTS provider, no outbound call, no audio file. This module is the
 * single seam over that API. Everything above it (content, controller, React
 * boundary) is browser-free and unit-testable; everything browser-specific —
 * voice enumeration, utterance construction, autoplay refusal — is here.
 *
 * Contract (`AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_
 * Implementation_Plan_V1.0.md` §8.2 — the vocabulary shared by every engine):
 *
 *   - `speak()` never throws and never rejects. It resolves with one **terminal
 *     outcome** — `completed`, `failed`, `interrupted`, `blocked`, `busy`,
 *     `unavailable` — so a queue operation can never be failed by audio.
 *   - `completed` is emitted **only** when the utterance reports `end`. A
 *     `start` event is progress, not proof: resolving on `start` is the F2
 *     defect this contract removes, because a browser that begins an utterance
 *     and then dies would otherwise be reported as a delivered announcement.
 *   - "returned without an exception" is NOT treated as proof of audio. An
 *     utterance that never fires `start` is reported as `blocked`, which is how
 *     a browser autoplay refusal actually looks.
 *   - one utterance at a time. A second call while speaking resolves `busy`
 *     rather than overlapping; `replace: true` cancels the first instead.
 *   - a language is never substituted. If Bangla is configured and no Bangla
 *     voice exists, the outcome is `unavailable` with `reason: 'voice_unavailable'`
 *     — an English voice is never used to read Bangla text.
 */

/** What the browser can do for a language right now. */
export const CAPABILITY = Object.freeze({
  UNSUPPORTED: 'unsupported',   // no speechSynthesis / no SpeechSynthesisUtterance
  PENDING: 'pending_voices',    // supported, but the voice list is still empty
  READY: 'ready',               // a voice for the requested language exists
  NO_VOICE: 'no_voice',         // voices exist, none for the requested language
});

/**
 * The terminal outcome of one playback attempt (§8.2). Every engine reports the
 * same six words; `reason` carries the specific cause.
 */
export const OUTCOME = Object.freeze({
  COMPLETED: 'completed',       // the engine reported that speech finished
  FAILED: 'failed',             // synthesis started but did not finish, or refused
  INTERRUPTED: 'interrupted',   // cancelled by us, by the page, or by the browser
  BLOCKED: 'blocked',           // refused before it began: autoplay policy / no start
  BUSY: 'busy',                 // another utterance is in progress
  UNAVAILABLE: 'unavailable',   // the engine cannot serve this language/voice
});
// D-6 (product owner, 2026-11-22): this is the *only* playback vocabulary.
// `completed` and `interrupted` are the approved words for a finished and a
// stopped sentence; the pre-merge spellings `spoken`/`cancelled`/`error`/
// `unsupported` were removed rather than aliased, so no engine, controller or
// persisted record can carry two names for one outcome.

/** BCP-47 tag used for each supported announcement language (OD-3). */
export const LANGUAGE_TAGS = Object.freeze({ bn: 'bn-BD', en: 'en-GB' });

/** Error codes a `SpeechSynthesisErrorEvent` may report. */
const CANCELLED_CODES = ['canceled', 'cancelled', 'interrupted'];
const BLOCKED_CODES = ['not-allowed', 'not-allowed-error', 'audio-busy', 'audio-hardware'];

function isLanguage(value) {
  return value === 'bn' || value === 'en';
}

function normaliseTag(value) {
  return String(value == null ? '' : value).toLowerCase().replace(/_/g, '-');
}

/**
 * Choose the best voice for a language, or `null` when there is none.
 *
 * A voice qualifies only if its own tag is that language (`bn` / `bn-*`).
 * Preference order is: the exact primary tag, then a local voice (a facility's
 * network may drop), then the browser default, then declaration order.
 *
 * @param {Array<{lang?: string, name?: string, localService?: boolean, default?: boolean}>} voices
 * @param {'bn'|'en'} language
 * @returns {{voice: object, voiceLang: string, name: string, matched: boolean, fallback: boolean}|null}
 */
export function pickVoice(voices, language) {
  if (!isLanguage(language)) return null;
  const primary = normaliseTag(LANGUAGE_TAGS[language]);

  const candidates = (Array.isArray(voices) ? voices : []).filter(
    (voice) => voice && typeof voice === 'object' && typeof voice.lang === 'string'
  );
  if (!candidates.length) return null;

  const bucket = candidates.filter((voice) => {
    const tag = normaliseTag(voice.lang);
    return tag === language || tag.startsWith(language + '-');
  });
  if (!bucket.length) return null;

  const rank = (voice) => {
    const tag = normaliseTag(voice.lang);
    let score = 0;
    if (tag !== primary) score += 8;                 // prefer the primary tag
    if (voice.localService !== true) score += 4;     // prefer a local voice
    if (voice.default !== true) score += 1;          // then the browser default
    return score;
  };

  const ordered = bucket.slice().sort((a, b) => rank(a) - rank(b));
  const voice = ordered[0];
  return {
    voice,
    voiceLang: voice.lang,
    name: typeof voice.name === 'string' ? voice.name : '',
    matched: normaliseTag(voice.lang) === primary,
    fallback: normaliseTag(voice.lang) !== primary,
  };
}

/**
 * Create the adapter over one `speechSynthesis` implementation.
 *
 * All environment access is injectable so the behaviour can be unit-tested
 * without a browser: `synth`, `Utterance`, `timers` and `startTimeoutMs`.
 *
 * @param {object} [options]
 * @param {object} [options.scope]  defaults to `window` when it exists
 * @param {object} [options.synth]  defaults to `scope.speechSynthesis`
 * @param {Function} [options.Utterance] defaults to `scope.SpeechSynthesisUtterance`
 * @param {{setTimeout: Function, clearTimeout: Function}} [options.timers]
 * @param {number} [options.startTimeoutMs] how long to wait for `start` (default 1500)
 */
export function createSpeechSynthesisAdapter(options = {}) {
  const scope = options.scope || (typeof window !== 'undefined' ? window : undefined);
  const synth = options.synth || (scope && scope.speechSynthesis) || null;
  const Utterance = options.Utterance || (scope && scope.SpeechSynthesisUtterance) || null;
  const timers = options.timers || {
    setTimeout: (fn, ms) => setTimeout(fn, ms),
    clearTimeout: (id) => clearTimeout(id),
  };
  const startTimeoutMs = Number.isFinite(options.startTimeoutMs) ? options.startTimeoutMs : 1500;
  // Upper bound for "started but never finished". Without it a stuck engine
  // leaves the controller believing it is speaking for ever.
  const endTimeoutMs = Number.isFinite(options.endTimeoutMs)
    ? Math.max(0, options.endTimeoutMs)
    : Math.max(5000, (typeof text === 'string' ? text.length : 0) * 250);
  const now = typeof options.now === 'function' ? options.now : () => Date.now();

  const supported = !!(
    synth
    && typeof synth.speak === 'function'
    && typeof synth.cancel === 'function'
    && typeof Utterance === 'function'
  );

  /** @type {null|{utterance: object, timer: any, resolve: Function}} */
  let current = null;
  const voiceListeners = new Set();
  let attached = false;
  let previousOnVoicesChanged;
  let disposed = false;

  function listVoices() {
    if (!supported) return [];
    try {
      const voices = synth.getVoices();
      return Array.isArray(voices) ? voices : [];
    } catch (err) {
      return [];
    }
  }

  /**
   * @param {'bn'|'en'} language
   * @returns {{status: string, language: string, voice: object|null, voices: object[]}}
   */
  function capability(language) {
    const lang = isLanguage(language) ? language : 'bn';
    if (!supported) return { status: CAPABILITY.UNSUPPORTED, language: lang, voice: null, voices: [] };
    const voices = listVoices();
    if (!voices.length) return { status: CAPABILITY.PENDING, language: lang, voice: null, voices };
    const picked = pickVoice(voices, lang);
    if (!picked) return { status: CAPABILITY.NO_VOICE, language: lang, voice: null, voices };
    return { status: CAPABILITY.READY, language: lang, voice: picked, voices };
  }

  function isSpeaking() {
    return current !== null;
  }

  function clearTimer() {
    if (current && current.timer != null) {
      timers.clearTimeout(current.timer);
      current.timer = null;
    }
    if (current && current.endTimer != null) {
      timers.clearTimeout(current.endTimer);
      current.endTimer = null;
    }
  }

  /** Cancel whatever is playing; the pending `speak()` resolves `interrupted`. */
  function cancel() {
    if (!supported) return;
    const pending = current;
    current = null;
    if (pending) {
      if (pending.timer != null) timers.clearTimeout(pending.timer);
      if (pending.endTimer != null) timers.clearTimeout(pending.endTimer);
      pending.resolve({ status: OUTCOME.INTERRUPTED, reason: 'cancelled' });
    }
    try { synth.cancel(); } catch (err) { /* a cancel must never throw upwards */ }
  }

  /**
   * Speak one utterance. Never throws, never rejects.
   *
   * @param {string} text
   * @param {{language?: 'bn'|'en', volume?: number, rate?: number,
   *          replace?: boolean, prime?: boolean}} [opts]
   *        `prime` skips language resolution: it exists only to unlock audio
   *        from a user gesture, so it must work before the voice list loads.
   * @returns {Promise<{status: string, language?: string, voice?: object|null,
   *                    reason?: string}>}
   */
  function speak(text, opts = {}) {
    const value = typeof text === 'string' ? text : '';
    if (disposed) return Promise.resolve({ status: OUTCOME.UNAVAILABLE, reason: 'disposed' });
    if (!value) return Promise.resolve({ status: OUTCOME.FAILED, reason: 'empty_text' });
    if (!supported) return Promise.resolve({ status: OUTCOME.UNAVAILABLE, reason: 'unsupported' });

    const language = isLanguage(opts.language) ? opts.language : 'bn';

    if (current) {
      if (!opts.replace) return Promise.resolve({ status: OUTCOME.BUSY, language });
      cancel();
    }

    let voice = null;
    if (!opts.prime) {
      const voices = listVoices();
      if (!voices.length) {
        return Promise.resolve({ status: OUTCOME.UNAVAILABLE, language, reason: 'voices_not_loaded' });
      }
      const picked = pickVoice(voices, language);
      // A missing language is reported, never substituted with another one.
      if (!picked) {
        return Promise.resolve({ status: OUTCOME.UNAVAILABLE, language, reason: 'voice_unavailable' });
      }
      voice = picked.voice;
    }

    let utterance;
    try {
      utterance = new Utterance(value);
    } catch (err) {
      return Promise.resolve({ status: OUTCOME.FAILED, language, reason: 'utterance_failed' });
    }

    try {
      if (voice) {
        utterance.voice = voice;
        utterance.lang = voice.lang;
      } else {
        utterance.lang = LANGUAGE_TAGS[language];
      }
      if (typeof opts.volume === 'number') utterance.volume = opts.volume;
      if (typeof opts.rate === 'number') utterance.rate = opts.rate;
    } catch (err) {
      // Some engines refuse `voice` assignment; the `lang` tag is still set.
    }

    return new Promise((resolve) => {
      let resolved = false;
      let startedAt = 0;
      const settle = (result) => {
        if (resolved) return;
        resolved = true;
        resolve(result);
      };
      const stopTracking = () => {
        if (current && current.utterance === utterance) {
          if (current.timer != null) timers.clearTimeout(current.timer);
          if (current.endTimer != null) timers.clearTimeout(current.endTimer);
          current = null;
        }
      };

      // `start` is progress, not an outcome. It proves the engine accepted the
      // utterance; only `end` proves the patient heard it (§8.1 rule 1).
      utterance.onstart = () => {
        startedAt = now();
        if (current && current.utterance === utterance) {
          if (current.timer != null) {
            timers.clearTimeout(current.timer);
            current.timer = null;
          }
          current.endTimer = timers.setTimeout(() => {
            if (current && current.utterance === utterance) {
              current = null;
              try { synth.cancel(); } catch (err) { /* ignore */ }
              settle({ status: OUTCOME.FAILED, language, reason: 'no_end_event' });
            }
          }, endTimeoutMs);
        }
        if (typeof utterance.onprogress === 'function') {
          try { utterance.onprogress({ phase: 'speaking' }); } catch (err) { /* progress only */ }
        }
      };

      utterance.onend = () => {
        stopTracking();
        settle({
          status: OUTCOME.COMPLETED,
          language,
          voice: voice ? { name: voice.name || '', lang: voice.lang || '' } : null,
          durationMs: startedAt ? Math.max(0, now() - startedAt) : 0,
        });
      };

      utterance.onerror = (event) => {
        stopTracking();
        const code = event && event.error ? String(event.error) : '';
        let status = OUTCOME.FAILED;
        let reason = code || 'synthesis_error';
        if (CANCELLED_CODES.includes(code)) {
          // A cancellation is an interruption whether or not `start` was
          // observed; only a blocked/refused engine or a silent engine is
          // reported as `blocked`.
          status = OUTCOME.INTERRUPTED;
        } else if (BLOCKED_CODES.includes(code)) {
          status = OUTCOME.BLOCKED;
        }
        settle({ status, language, reason });
      };

      current = {
        utterance,
        resolve: settle,
        timer: timers.setTimeout(() => {
          // No `start` event: the browser refused to play (autoplay policy or no
          // output device). Treat silence as a refusal, never as success.
          if (current && current.utterance === utterance) {
            current = null;
            try { synth.cancel(); } catch (err) { /* ignore */ }
            settle({ status: OUTCOME.BLOCKED, language, reason: 'no_start_event' });
          }
        }, startTimeoutMs),
        endTimer: null,
      };

      try {
        synth.speak(utterance);
      } catch (err) {
        stopTracking();
        settle({ status: OUTCOME.FAILED, language, reason: 'speak_threw' });
      }
    });
  }

  function notifyVoices() {
    const voices = listVoices();
    Array.from(voiceListeners).forEach((listener) => {
      try { listener(voices); } catch (err) { /* a listener must not break speech */ }
    });
  }

  function attachVoiceListener() {
    if (attached || !supported) return;
    if (typeof synth.addEventListener === 'function') {
      synth.addEventListener('voiceschanged', notifyVoices);
    } else {
      // Fallback for engines that only expose the property handler. The previous
      // value is restored on dispose so nothing else on the page is disturbed.
      previousOnVoicesChanged = synth.onvoiceschanged;
      synth.onvoiceschanged = notifyVoices;
    }
    attached = true;
  }

  function detachVoiceListener() {
    if (!attached) return;
    if (typeof synth.removeEventListener === 'function') {
      synth.removeEventListener('voiceschanged', notifyVoices);
    } else {
      synth.onvoiceschanged = previousOnVoicesChanged;
    }
    attached = false;
  }

  /**
   * Re-read the voice list whenever the browser publishes new voices.
   * Chrome ships `getVoices()` empty and fills it asynchronously, so a client
   * that only read once would report "no voice" forever.
   *
   * @param {(voices: object[]) => void} listener
   * @returns {() => void} unsubscribe
   */
  function subscribeVoices(listener) {
    if (typeof listener !== 'function' || !supported) return () => {};
    voiceListeners.add(listener);
    attachVoiceListener();
    return () => {
      voiceListeners.delete(listener);
      if (!voiceListeners.size) detachVoiceListener();
    };
  }

  /** Stop speech, drop listeners and refuse further playback. */
  function dispose() {
    cancel();
    voiceListeners.clear();
    detachVoiceListener();
    disposed = true;
  }

  return {
    isSupported: () => supported,
    isSpeaking,
    listVoices,
    capability,
    pickVoice: (language) => pickVoice(listVoices(), language),
    speak,
    cancel,
    subscribeVoices,
    dispose,
  };
}


