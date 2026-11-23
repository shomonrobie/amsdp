/* QUE-006 / W1 — prerecorded announcement player.
 *
 * Transport only. Every decision stays in `controller.js` (dedupe, overlap,
 * activation); this module takes a resolved segment list and plays the files in
 * order through one `Audio` element at a time.
 *
 * Contract, and why each clause exists:
 *   - `completed` is resolved **only** after the final segment's `ended` event
 *     (roadmap §8.1 AC-2). A promise that resolved is not evidence of sound, so
 *     nothing else is reported as success.
 *   - a missing asset fails the whole announcement **before** any element is
 *     created (AC-3) — no partial sentence, no speech-synthesis fallback.
 *   - a corrupt file resolves `failed('decode_error')` and the engine stays
 *     usable for the next announcement (AC-4).
 *   - a second `play()` while one is running resolves `busy` (AC-5); the caller
 *     decides whether that is acceptable, this module never queues audio.
 *   - nothing is fetched: the segment's `src` is a local path under the pack's
 *     `basePath`, so an installed catalogue plays offline (AC-6).
 *   - `play()` never rejects. A queue operation cannot be failed by audio
 *     (assignment §3.3, §8.5).
 *
 * Interruption vs cancellation: `cancel()` is ours and resolves
 * `interrupted` (D-6: the approved word for a playback that started and was
 * stopped); anything else that stops the element mid-clip (a pause we did not
 * ask for, an aborted media error) resolves `failed('interrupted')`, which is
 * the honest report for "the sentence stopped without anyone asking".
 */
import { joinBasePath, normalisePack, resolveSegments, SEGMENT_KIND } from './segments.js';

/** The outcome of one playback attempt. */
export const PLAYBACK = Object.freeze({
  COMPLETED: 'completed',
  FAILED: 'failed',
  BUSY: 'busy',
  INTERRUPTED: 'interrupted',
});

/** Why an attempt did not complete. */
export const FAILURE = Object.freeze({
  MISSING_ASSET: 'missing_asset',
  DECODE_ERROR: 'decode_error',
  INTERRUPTED: 'interrupted',
  NETWORK_ERROR: 'network_error',
  UNSUPPORTED_SOURCE: 'unsupported_source',
  BLOCKED: 'blocked',
  AUDIO_UNAVAILABLE: 'audio_unavailable',
  UNSUPPORTED_LANGUAGE: 'unsupported_language',
  UNSPEAKABLE_TOKEN: 'unspeakable_token',
  UNSPEAKABLE_ROOM: 'unspeakable_room',
  MANIFEST_UNAVAILABLE: 'manifest_unavailable',
  NO_VOICE_PACK: 'no_voice_pack',
  ERROR: 'error',
});

const MEDIA_ERR_ABORTED = 1;
const MEDIA_ERR_NETWORK = 2;
const MEDIA_ERR_DECODE = 3;

/**
 * Map a `MediaError` from the element to a reported reason.
 * @param {{code?: number}|null|undefined} error
 */
export function reasonForMediaError(error) {
  const code = error && Number(error.code);
  if (code === MEDIA_ERR_ABORTED) return FAILURE.INTERRUPTED;
  if (code === MEDIA_ERR_NETWORK) return FAILURE.NETWORK_ERROR;
  if (code === MEDIA_ERR_DECODE) return FAILURE.DECODE_ERROR;
  if (code === 4) return FAILURE.UNSUPPORTED_SOURCE;
  return FAILURE.ERROR;
}

function defaultAudioFactory(src) {
  if (typeof Audio === 'undefined') throw new Error('no Audio in this environment');
  return new Audio(src);
}

const defaultTimers = {
  setTimeout: (fn, ms) => setTimeout(fn, ms),
  clearTimeout: (id) => clearTimeout(id),
};

const SEGMENT_EVENTS = ['ended', 'error', 'pause', 'abort', 'stalled'];

/**
 * Create a player over one voice pack.
 *
 * @param {object} [options]
 * @param {object} [options.pack] pack descriptor (see `segments.resolveSegments`)
 * @param {() => object} [options.packProvider] resolved on every `play()`, for
 *        a configured pack that can change without re-creating the player
 * @param {(src: string) => object} [options.audioFactory] injectable `Audio`
 * @param {{setTimeout: Function, clearTimeout: Function}} [options.timers]
 * @param {(outcome: object) => void} [options.logger]
 */
export function createPrerecordedPlayer(options = {}) {
  const audioFactory = typeof options.audioFactory === 'function'
    ? options.audioFactory : defaultAudioFactory;
  const timers = options.timers && typeof options.timers.setTimeout === 'function'
    ? options.timers : defaultTimers;
  const logger = typeof options.logger === 'function' ? options.logger : null;

  let pack = options.pack || null;
  let playing = false;
  let cancelled = false;
  let currentAudio = null;
  let pauseTimer = null;
  let pauseResolve = null;
  let last = null;
  let disposed = false;

  function activePack() {
    if (typeof options.packProvider === 'function') {
      try {
        return options.packProvider();
      } catch (err) {
        return null;
      }
    }
    return pack;
  }

  function remember(result) {
    last = result;
    if (logger) {
      try { logger(result); } catch (err) { /* a logger must never break playback */ }
    }
    return result;
  }

  function wait(ms) {
    return new Promise((resolve) => {
      pauseResolve = resolve;
      pauseTimer = timers.setTimeout(() => {
        pauseTimer = null;
        pauseResolve = null;
        resolve();
      }, ms);
    });
  }

  function clearPause() {
    if (pauseTimer != null) {
      timers.clearTimeout(pauseTimer);
      pauseTimer = null;
    }
    if (pauseResolve) {
      const resolve = pauseResolve;
      pauseResolve = null;
      resolve();
    }
  }

  function playSegment(segment) {
    return new Promise((resolve) => {
      let element;
      try {
        element = audioFactory(segment.src);
      } catch (err) {
        resolve({ status: PLAYBACK.FAILED, reason: FAILURE.AUDIO_UNAVAILABLE });
        return;
      }
      if (!element || typeof element.play !== 'function'
          || typeof element.addEventListener !== 'function') {
        resolve({ status: PLAYBACK.FAILED, reason: FAILURE.AUDIO_UNAVAILABLE });
        return;
      }
      currentAudio = element;
      let settled = false;

      function detach() {
        if (typeof element.removeEventListener !== 'function') return;
        SEGMENT_EVENTS.forEach((name) => {
          element.removeEventListener(name, handlers[name]);
        });
      }
      function done(result) {
        if (settled) return;
        settled = true;
        detach();
        if (currentAudio === element) currentAudio = null;
        resolve(result);
      }

      // A clip that reaches its end is *paused* before `ended` fires: the HTML
      // media element's "ended playback" steps set `ended`, then queue `pause`,
      // then `ended`.  Reading that pause as an interruption reported every
      // natural ending as `failed('interrupted')`, which in a real browser meant
      // the activation prime never reported `primed` — so the queue page could
      // never leave "audio off" and no announcement ever played — and a clip
      // that had finished was recorded as a failure.  A pause taken at the end
      // of the media is completion.
      function playedToEnd() {
        if (element.ended === true) return true;
        const duration = Number(element.duration);
        const time = Number(element.currentTime);
        return Number.isFinite(duration) && duration > 0
          && Number.isFinite(time) && time >= duration - 0.05;
      }

      const handlers = {
        ended: () => done({ status: PLAYBACK.COMPLETED }),
        error: () => done({
          status: PLAYBACK.FAILED, reason: reasonForMediaError(element.error) }),
        pause: () => {
          if (!cancelled && playedToEnd()) {
            done({ status: PLAYBACK.COMPLETED });
            return;
          }
          done(cancelled
            ? { status: PLAYBACK.INTERRUPTED, reason: 'cancelled' }
            : { status: PLAYBACK.FAILED, reason: FAILURE.INTERRUPTED });
        },
        abort: () => done(cancelled
          ? { status: PLAYBACK.INTERRUPTED, reason: 'cancelled' }
          : { status: PLAYBACK.FAILED, reason: FAILURE.INTERRUPTED }),
        stalled: () => done({ status: PLAYBACK.FAILED, reason: FAILURE.NETWORK_ERROR }),
      };
      SEGMENT_EVENTS.forEach((name) => element.addEventListener(name, handlers[name]));

      try {
        const started = element.play();
        if (started && typeof started.then === 'function') {
          started.then(null, () => done({
            status: PLAYBACK.FAILED, reason: FAILURE.BLOCKED }));
        }
      } catch (err) {
        done({ status: PLAYBACK.FAILED, reason: FAILURE.BLOCKED });
      }
    });
  }

  async function run(resolved) {
    let completed = 0;
    for (const segment of resolved.segments) {
      if (cancelled) {
        return { status: PLAYBACK.INTERRUPTED, reason: 'cancelled', completedSegments: completed };
      }
      if (segment.kind === SEGMENT_KIND.PAUSE) {
        if (segment.durationMs > 0) await wait(segment.durationMs);
        if (cancelled) {
          return { status: PLAYBACK.INTERRUPTED, reason: 'cancelled', completedSegments: completed };
        }
        completed += 1;
        continue;
      }
      const step = await playSegment(segment);
      if (step.status !== PLAYBACK.COMPLETED) {
        return {
          status: step.status,
          reason: step.reason,
          completedSegments: completed,
          failedAssetId: segment.assetId,
        };
      }
      completed += 1;
    }
    // Only reachable when the final segment reported `ended` — AC-2.
    return { status: PLAYBACK.COMPLETED, completedSegments: completed };
  }

  /**
   * Play one announcement.
   * @param {{token?: unknown, room?: unknown}} input
   * @returns {Promise<object>} never rejects
   */
  async function play(input = {}) {
    if (disposed) {
      return remember({ status: PLAYBACK.FAILED, reason: FAILURE.AUDIO_UNAVAILABLE });
    }
    if (playing) {
      // No queueing and no overlap: the caller owns the policy (AC-5).
      return { status: PLAYBACK.BUSY, reason: 'in_progress' };
    }

    const resolved = resolveSegments(input, activePack());
    if (!resolved.ok) {
      const result = {
        status: PLAYBACK.FAILED,
        reason: resolved.reason,
        packId: resolved.packId || '',
      };
      if (resolved.missing) result.missing = resolved.missing;
      return remember(result);
    }

    playing = true;
    cancelled = false;
    let result;
    try {
      result = await run(resolved);
    } catch (err) {
      result = { status: PLAYBACK.FAILED, reason: FAILURE.ERROR };
    } finally {
      playing = false;
      cancelled = false;
      currentAudio = null;
      clearPause();
    }
    return remember({
      ...result,
      packId: resolved.packId,
      version: resolved.version,
      language: resolved.language,
      segmentCount: resolved.segments.length,
      approvedText: resolved.approvedText,
    });
  }

  /** Stop the announcement in progress. `play()` then resolves `cancelled`. */
  function cancel() {
    if (!playing) return false;
    cancelled = true;
    clearPause();
    if (currentAudio && typeof currentAudio.pause === 'function') {
      try { currentAudio.pause(); } catch (err) { /* the promise already settles */ }
    }
    return true;
  }

  /**
   * Point the player at a different pack version (W3/W5 switch voices).
   * Refused while an announcement is in progress, so a sentence can never
   * change voice halfway through.
   */
  function setPack(next) {
    if (playing) return false;
    pack = next || null;
    return true;
  }

  function getState() {
    const active = activePack();
    return {
      playing,
      packId: active && typeof active.id === 'string' ? active.id : '',
      language: active && typeof active.language === 'string' ? active.language : '',
      version: active && Number.isFinite(active.version) ? active.version : 0,
      last,
    };
  }

  /** What the configured pack can do right now, without playing anything. */
  function capability() {
    const active = activePack();
    if (!active) {
      // No pack yet (the manifest may still be loading): "pending", not
      // "no voice" — a missing catalogue is not the same as a missing voice.
      return { status: 'pending', packId: '', language: '', version: 0, assets: 0 };
    }
    const normalised = normalisePack(active);
    const playable = normalised.assets.some(
      (asset) => asset && typeof asset.playbackFile === 'string' && asset.playbackFile);
    return {
      status: playable ? 'ready' : 'no_voice',
      packId: normalised.id,
      language: normalised.language,
      version: normalised.version,
      assets: normalised.assets.length,
    };
  }

  /**
   * Unlock playback from an operator gesture.
   *
   * A browser only unlocks audio inside a gesture, so something must be played
   * from the click. The catalogue's `intentional-pause` clip is 300 ms of
   * silence by construction, so priming is inaudible and speaks no wording. If
   * a pack has no such clip the prime reports `unavailable` rather than playing
   * a real announcement out of context.
   *
   * @returns {Promise<{status: string, reason?: string}>} never rejects
   */
  async function prime() {
    if (disposed) return { status: 'unavailable', reason: FAILURE.AUDIO_UNAVAILABLE };
    if (playing) return { status: PLAYBACK.BUSY, reason: 'in_progress' };
    const normalised = normalisePack(activePack());
    const silent = normalised.assets.find((asset) => asset
      && asset.contentStatus === 'intentional-pause'
      && typeof asset.playbackFile === 'string' && asset.playbackFile);
    if (!silent) return { status: 'unavailable', reason: 'no_prime_asset' };

    playing = true;
    cancelled = false;
    let step;
    try {
      step = await playSegment({
        assetId: silent.id,
        src: joinBasePath(normalised.basePath, silent.playbackFile),
      });
    } finally {
      playing = false;
      cancelled = false;
      currentAudio = null;
      clearPause();
    }
    if (step.status === PLAYBACK.COMPLETED) return { status: 'primed' };
    return { status: step.status === PLAYBACK.INTERRUPTED ? 'interrupted' : 'failed', reason: step.reason };
  }

  function dispose() {
    cancel();
    disposed = true;
    pack = null;
  }

  return { play, prime, cancel, setPack, getState, capability, dispose };
}
