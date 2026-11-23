/**
 * ElevenLabs text-to-speech client — REST only, no SDK dependency.
 *
 * Contract source (read 2026-11-20):
 *   https://elevenlabs.io/docs/api-reference/text-to-speech/convert.md
 *   https://elevenlabs.io/docs/models.md
 *
 *   POST {base}/text-to-speech/{voice_id}?output_format=wav_24000
 *   header: xi-api-key            (not `Authorization: Bearer`, not x-goog-api-key)
 *   body:   { text, model_id }
 *   result: raw audio bytes — for a `wav_*` format the body is already a complete
 *           WAV file, so no container has to be invented here.
 *
 * Facts taken from that page and deliberately encoded below:
 *   - `output_format` defaults to `mp3_44100_128`; the allowed values are the
 *     alaw_8000 / mp3_* / opus_* / pcm_* / ulaw_8000 / wav_* enums.
 *   - "PCM and WAV formats with 44.1kHz sample rate requires you to be
 *     subscribed to Pro tier or above." Therefore `wav_44100` / `pcm_44100` are
 *     **not** assumed to work on this account, and the default is `wav_24000`.
 *     24 kHz is also what the Gemini path produced, so the clips stay comparable.
 *   - `language_code` "is not supported for multilingual_v2 models" — never sent.
 *   - `enable_logging` defaults to true and zero-retention mode is enterprise
 *     only, so the default is left alone; the README states that request text
 *     appears in the account's request history.
 *   - Residency hosts exist (us / eu / in / sg); `ELEVENLABS_API_BASE` can point
 *     at one, because an organisation may be pinned to a region.
 *
 * Why `wav_*` and never `pcm_*`: a WAV body carries its own sample rate, bit
 * depth and channel count, so nothing in this utility has to *assume* 16-bit
 * samples and quietly mis-declare a header. `pcm_*` is rejected by
 * `provider.mjs` with a message that says so.
 *
 * Whether a voice can actually speak Bangla is **not** asserted here: the model
 * page lists 29 languages for `eleven_multilingual_v2` but its language list was
 * not retrievable (HTTP 403), so the preflight probe is the only evidence the
 * utility accepts. See the implementation report.
 */

import { redact } from './env.mjs';
import { TtsError } from './tts-error.mjs';

export const PROVIDER = 'elevenlabs';

export const DEFAULT_API_BASE = 'https://api.elevenlabs.io/v1';
export const DEFAULT_MODEL = 'eleven_multilingual_v2';
/** Documented as the fast/cheap alternative; offered by `--model`, not used by default. */
export const FAST_MODEL = 'eleven_flash_v2_5';
export const DEFAULT_OUTPUT_FORMAT = 'wav_24000';
export const DEFAULT_TIMEOUT_MS = 120_000;

/** Every value the API documents for `output_format`. Anything else is refused. */
export const ALLOWED_OUTPUT_FORMATS = [
  'alaw_8000',
  'mp3_22050_32', 'mp3_24000_48', 'mp3_44100_32', 'mp3_44100_64', 'mp3_44100_96',
  'mp3_44100_128', 'mp3_44100_192',
  'opus_48000_32', 'opus_48000_64', 'opus_48000_96', 'opus_48000_128', 'opus_48000_192',
  'pcm_8000', 'pcm_16000', 'pcm_22050', 'pcm_24000', 'pcm_32000', 'pcm_44100', 'pcm_48000',
  'ulaw_8000',
  'wav_8000', 'wav_16000', 'wav_22050', 'wav_24000', 'wav_32000', 'wav_44100', 'wav_48000',
];

/** Formats the API gates behind a paid tier, per the same documentation page. */
export const TIER_GATED_FORMATS = ['mp3_44100_192', 'pcm_44100', 'wav_44100'];

export class ElevenLabsError extends TtsError {
  constructor(message, info = {}) {
    super(message, { provider: PROVIDER, ...info });
    this.name = 'ElevenLabsError';
  }
}

/** `wav_24000` -> 'wav'. Unknown shapes return 'unknown' rather than guessing. */
export function formatFamily(outputFormat) {
  const match = /^([a-z]+)_(\d+)/.exec(String(outputFormat || ''));
  return match ? match[1] : 'unknown';
}

/** `wav_24000` -> 24000. Used only for reporting, never to build a header. */
export function sampleRateFromFormat(outputFormat) {
  const match = /_(\d+)(?:_\d+)?$/.exec(String(outputFormat || ''));
  return match ? Number(match[1]) : null;
}

/** Is this an `output_format` the API documents? */
export function isAllowedOutputFormat(outputFormat) {
  return ALLOWED_OUTPUT_FORMATS.includes(String(outputFormat || ''));
}

/**
 * Read the message out of an ElevenLabs error body.
 *
 * Three shapes occur and all three are parsed without throwing:
 *   { "detail": { "status": "invalid_api_key", "message": "Invalid API key" } }
 *   { "detail": [ { "loc": [...], "msg": "...", "type": "..." } ] }   (422)
 *   { "detail": "..." }
 */
export function parseErrorBody(bodyText) {
  const text = String(bodyText || '');
  let status = '';
  let message = '';
  try {
    const parsed = JSON.parse(text);
    const detail = parsed?.detail ?? parsed;
    if (typeof detail === 'string') {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail
        .map((entry) => entry?.msg || entry?.message || JSON.stringify(entry))
        .filter(Boolean)
        .join('; ');
    } else if (detail && typeof detail === 'object') {
      status = String(detail.status || '');
      message = String(detail.message || detail.msg || '');
    }
    if (!message && parsed?.message) message = String(parsed.message);
  } catch {
    message = text.slice(0, 500);
  }
  return { status, message: message || text.slice(0, 500) };
}

/**
 * Classify an HTTP failure into something the caller can act on.
 *
 * `stopRun` marks failures where continuing would only burn quota: a rejected
 * key, a tier restriction, an exhausted character quota, or a voice id the
 * account does not own. A concurrency 429 is deliberately **retryable without
 * stopping**, because the free plan allows only two simultaneous requests and
 * this utility generates sequentially — a 429 there is transient.
 *
 * @param {number} status
 * @param {string} bodyText
 * @param {string|null} secret
 * @param {{retryAfter?: string|null}} [headers]
 */
export function classifyHttpError(status, bodyText, secret = null, headers = {}) {
  const { status: detailStatus, message } = parseErrorBody(bodyText);
  const detail = redact(`${detailStatus ? `${detailStatus}: ` : ''}${message}`, secret).slice(0, 600);
  const haystack = `${detailStatus} ${message}`;

  // A key that authenticates but is scoped too narrowly is NOT a rejected key,
  // yet ElevenLabs reports both with HTTP 401 — the difference is only in the body
  // (`detail.status` = `missing_permissions`). Verified against the live API on
  // 2026-11-21: a genuine key without the `voices_read` scope answered
  // `401 missing_permissions: The API key you used is missing the permission
  // voices_read to execute this operation.` Filing that as "key rejected" sent the
  // reader off to re-copy a key that was already correct, so permission scope is
  // matched first and named explicitly.
  const permissionMatch = /missing_permissions|missing the permission\s+([a-z0-9_,\s]+?)\s+to execute/i.exec(haystack);
  if (permissionMatch) {
    // The alternation above matches the bare token first, so the scope name has to
    // be read separately from the sentence that carries it.
    const scopeMatch = /missing the permission\s+([a-z0-9_,\s]+?)\s+to execute/i.exec(haystack);
    const scope = scopeMatch ? scopeMatch[1].replace(/\s+/g, ' ').trim() : '';
    const named = scope ? `\`${scope}\`` : 'the scope this call requires';
    return new ElevenLabsError(`key lacks permission (${status}): ${detail}`, {
      kind: 'key-permissions', status, stopRun: true,
      guidance: `The key was accepted, so it is a real key — but it is not scoped for this call: `
        + `it is missing ${named}. In elevenlabs.io -> Profile -> API Keys, edit or create a key with `
        + 'the `voices_read` scope (needed by --list-voices and the probe) and the `text_to_speech` '
        + 'scope (needed to generate audio), then re-run --preflight-only. Re-copying the same key '
        + 'cannot fix a missing scope.',
    });
  }

  // A rejected key is 401 here (unlike Google's 400). Checked first so the
  // guidance cannot end up blaming the voice id or the text.
  const keyRejected = status === 401
    || /invalid_api_key|invalid api key|xi-api-key.*(?:invalid|missing)|api key is (?:invalid|missing)/i.test(haystack);
  if (keyRejected) {
    return new ElevenLabsError(`key rejected by ElevenLabs (${status}): ${detail}`, {
      kind: 'api-key-invalid', status, stopRun: true,
      guidance: 'ElevenLabs rejected the key itself, so no model, voice or text change will help. '
        + 'Re-copy the complete key from elevenlabs.io -> Profile -> API Keys into ELEVEN_LABS_API_KEY '
        + '(or .env.local) and re-run --preflight-only.',
    });
  }

  const quota = /quota_exceeded|not_enough_credits|character_limit|exceeds? (?:your|the) quota|insufficient/i.test(haystack)
    || status === 402;
  if (quota) {
    return new ElevenLabsError(`quota exhausted (${status}): ${detail}`, {
      kind: 'quota', status, stopRun: true,
      guidance: 'The account character quota for this period is used up. Wait for the period to reset; '
        + 'do not upgrade the plan without project-owner approval. Already-generated clips are skipped on re-run and are not re-billed.',
    });
  }

  const planGated = /requires? (?:you )?to be subscribed|pro tier|creator tier|paid plan|upgrade your (?:plan|subscription)/i.test(haystack);
  if (planGated) {
    return new ElevenLabsError(`format or voice not available on this plan (${status}): ${detail}`, {
      kind: 'plan-restricted', status, stopRun: true,
      guidance: `The account tier does not allow this request. Use a lower output_format — the default ${DEFAULT_OUTPUT_FORMAT} `
        + 'needs no paid tier — or choose a voice the account owns. Do not change plan without owner approval.',
    });
  }

  if (status === 403) {
    return new ElevenLabsError(`access denied (403): ${detail}`, {
      kind: 'permission', status, stopRun: true,
      guidance: 'The key is valid but not permitted for this resource (workspace permissions, voice ownership or region).',
    });
  }
  if (status === 404) {
    return new ElevenLabsError(`not found (404): ${detail}`, {
      kind: 'not-found', status, stopRun: true,
      guidance: 'The voice id or model id does not exist for this account. Run --list-voices to see the ids that do.',
    });
  }
  if (status === 422 || status === 400) {
    return new ElevenLabsError(`request rejected (${status}): ${detail}`, {
      kind: 'bad-request', status,
      guidance: 'Check the model id, voice id, output_format and text length; this request will not succeed unchanged.',
    });
  }
  if (status === 429) {
    const retryAfter = headers.retryAfter ? ` Retry-After: ${headers.retryAfter}s.` : '';
    return new ElevenLabsError(`rate limited (429): ${detail}`, {
      kind: 'rate-limited', status, retryable: true, stopRun: false,
      guidance: `Concurrency or rate limit reached.${retryAfter} The utility already generates one request at a time and backs off.`,
    });
  }
  if (status >= 500) {
    return new ElevenLabsError(`server error (${status}): ${detail}`, {
      kind: 'server', status, retryable: true,
      guidance: 'Transient ElevenLabs-side failure; retrying is safe.',
    });
  }
  return new ElevenLabsError(`unexpected HTTP ${status}: ${detail}`, { kind: 'unknown', status, detail });
}

/**
 * One HTTP call. Audio responses are returned as bytes; everything else as JSON.
 *
 * @param {string} apiBase
 * @param {string} apiKey
 * @param {string} pathname
 * @param {{method?: string, body?: unknown, timeoutMs?: number, expect?: 'json'|'bytes'}} [options]
 */
export async function request(apiBase, apiKey, pathname, options = {}) {
  const method = options.method || 'GET';
  const expect = options.expect || 'json';
  const url = `${apiBase.replace(/\/+$/, '')}${pathname}`;
  const headers = { 'xi-api-key': apiKey };
  if (options.body !== undefined) headers['content-type'] = 'application/json';

  let response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: AbortSignal.timeout(options.timeoutMs ?? DEFAULT_TIMEOUT_MS),
    });
  } catch (err) {
    const timedOut = err?.name === 'TimeoutError' || err?.name === 'AbortError';
    const reason = timedOut
      ? `request timed out after ${options.timeoutMs ?? DEFAULT_TIMEOUT_MS} ms`
      : `network error: ${err?.message || 'unknown'}`;
    throw new ElevenLabsError(redact(reason, apiKey), {
      kind: 'network', retryable: true, guidance: 'Check connectivity and retry.',
    });
  }

  if (!response.ok) {
    const text = await response.text();
    throw classifyHttpError(response.status, text, apiKey, {
      retryAfter: response.headers.get('retry-after'),
    });
  }

  if (expect === 'bytes') {
    const contentType = response.headers.get('content-type') || '';
    const bytes = Buffer.from(await response.arrayBuffer());
    if (/application\/json/i.test(contentType)) {
      // A 200 carrying JSON is a contract change, not audio: fail loudly with the
      // body recorded rather than writing a "wav" that is really an error message.
      const text = bytes.toString('utf8');
      throw new ElevenLabsError(`expected audio, received ${contentType}`, {
        kind: 'protocol', status: response.status,
        guidance: `The response body was JSON where audio was expected: ${redact(text, apiKey).slice(0, 300)}`,
      });
    }
    return { status: response.status, contentType, bytes };
  }

  const text = await response.text();
  let json = null;
  if (text) {
    try {
      json = JSON.parse(text);
    } catch {
      throw new ElevenLabsError('response was not valid JSON', { kind: 'protocol', status: response.status });
    }
  }
  return { status: response.status, json, text };
}

/**
 * Synthesise one transcript to audio.
 *
 * @param {object} options
 * @param {string} options.apiBase
 * @param {string} options.apiKey
 * @param {string} options.model
 * @param {string} options.voice       ElevenLabs voice id
 * @param {string} options.text
 * @param {string} [options.outputFormat]
 * @param {object|null} [options.voiceSettings]
 * @param {number} [options.timeoutMs]
 * @returns {Promise<{buffer: Buffer, outputFormat: string, contentType: string,
 *   responsePath: string, status: number}>}
 */
export async function synthesize(options) {
  const outputFormat = options.outputFormat || DEFAULT_OUTPUT_FORMAT;
  if (!isAllowedOutputFormat(outputFormat)) {
    throw new ElevenLabsError(`unsupported output_format "${outputFormat}"`, {
      kind: 'config', stopRun: true,
      guidance: `Use one of the documented values, e.g. ${DEFAULT_OUTPUT_FORMAT}. Full list: ${ALLOWED_OUTPUT_FORMATS.join(', ')}.`,
    });
  }
  if (!options.voice) {
    throw new ElevenLabsError('no voice id configured', {
      kind: 'config', stopRun: true,
      guidance: 'Set ELEVENLABS_VOICE_ID_EN / ELEVENLABS_VOICE_ID_BN (or pass --voice-en/--voice-bn). '
        + 'Run --list-voices to see the ids this account can use.',
    });
  }

  const body = { text: options.text, model_id: options.model };
  // `language_code` is documented as unsupported for multilingual_v2, so it is
  // never sent; `voice_settings` is only included when explicitly configured.
  if (options.voiceSettings) body.voice_settings = options.voiceSettings;

  const pathname = `/text-to-speech/${encodeURIComponent(options.voice)}?output_format=${encodeURIComponent(outputFormat)}`;
  const { status, contentType, bytes } = await request(options.apiBase, options.apiKey, pathname, {
    method: 'POST',
    body,
    expect: 'bytes',
    timeoutMs: options.timeoutMs,
  });

  if (bytes.length < 64) {
    throw new ElevenLabsError(`audio payload is only ${bytes.length} bytes`, {
      kind: 'protocol', status,
      guidance: 'Too small to be any audio container; nothing was written.',
    });
  }

  return {
    buffer: bytes,
    outputFormat,
    contentType: contentType || null,
    responsePath: `POST /text-to-speech/{voice_id} (${outputFormat})`,
    status,
  };
}

/**
 * List the models the key can see, so preflight can prove the configured model
 * exists and can actually do speech. `can_do_text_to_speech` is the field the
 * documentation points at, so it is surfaced rather than assumed.
 *
 * @param {string} apiBase
 * @param {string} apiKey
 */
export async function listModels(apiBase, apiKey) {
  const { json } = await request(apiBase, apiKey, '/models');
  const models = Array.isArray(json) ? json : (Array.isArray(json?.models) ? json.models : []);
  return models.map((model) => ({
    modelId: String(model.model_id || model.modelId || ''),
    name: model.name || null,
    canDoTextToSpeech: Boolean(model.can_do_text_to_speech ?? model.canDoTextToSpeech),
    languages: Array.isArray(model.languages) ? model.languages.map((entry) => entry.language || entry) : [],
  }));
}

/**
 * List voices owned by / shared with the account, including the label set that
 * carries `language` and `accent`, so choosing a Bangla voice is a decision made
 * from data rather than a guess at an id.
 *
 * @param {string} apiBase
 * @param {string} apiKey
 */
export async function listVoices(apiBase, apiKey) {
  const { json } = await request(apiBase, apiKey, '/voices');
  const voices = Array.isArray(json?.voices) ? json.voices : [];
  return voices.map((voice) => ({
    voiceId: String(voice.voice_id || voice.voiceId || ''),
    name: voice.name || null,
    category: voice.category || null,
    labels: voice.labels && typeof voice.labels === 'object' ? voice.labels : {},
    description: voice.description || null,
    previewUrl: voice.preview_url || null,
  }));
}

/** True when a model id looks like a documented ElevenLabs TTS model. */
export function isTtsModelName(modelId) {
  return /eleven_(?:multilingual|turbo|flash|v\d)/i.test(String(modelId || ''));
}

