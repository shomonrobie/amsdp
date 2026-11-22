/**
 * Gemini text-to-speech client — REST only, no SDK dependency.
 *
 * Contract source (verified 2026-11-20):
 *   - https://ai.google.dev/gemini-api/docs/speech-generation
 *   - https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts
 *
 *   POST {base}/interactions      base = https://generativelanguage.googleapis.com/v1beta
 *   header: x-goog-api-key        keeps the key out of URLs and logs
 *   body:   { model, input, response_format: {type: "audio"},
 *             generation_config: { speech_config: [ { voice } ] }, store: false }
 *   result: base64 audio in `output_audio.data`, `audio/wav`, 24 kHz
 *
 * `gemini-3.8-flash-tts` lists **Bangla** among its 130 supported languages, so
 * Bangla and English share one model and differ only by voice and input text.
 *
 * The response reader is tolerant by design: it looks for the audio in the
 * documented `output_audio` field first, then in execution steps, then in any
 * nested object carrying base64 data with an `audio/*` MIME type, and reports
 * which path it used. Schema drift then surfaces as a recorded fact instead of a
 * silent empty file.
 */

import { redact } from './env.mjs';
import { TtsError } from './tts-error.mjs';

export const DEFAULT_API_BASE = 'https://generativelanguage.googleapis.com/v1beta';
export const DEFAULT_MODEL = 'gemini-3.8-flash-tts';
export const DEFAULT_VOICE = 'Kore';
export const DEFAULT_TIMEOUT_MS = 120_000;
export const INTERACTIONS_PATH = '/interactions';

/**
 * Error carrying a classification the caller can act on, so a quota or
 * permission problem stops the run instead of burning retries across 28 assets.
 *
 * Extends the shared `TtsError` so `generate.mjs` retries and stops on the same
 * conditions regardless of which provider raised the failure.
 */
export class GeminiError extends TtsError {
  /**
   * @param {string} message
   * @param {{kind: string, status?: number|null, retryable?: boolean,
   *   stopRun?: boolean, guidance?: string, detail?: string}} info
   */
  constructor(message, info) {
    super(message, { provider: 'gemini', ...info });
    this.name = 'GeminiError';
  }
}


/**
 * Classify an HTTP failure. `stopRun` marks failures where continuing is
 * pointless or harmful: a rejected key, a project without access, exhausted
 * quota, or a model the key cannot see.
 *
 * @param {number} status
 * @param {string} bodyText
 * @param {string|null} secret
 */
export function classifyHttpError(status, bodyText, secret = null) {
  let apiMessage = '';
  try {
    const parsed = JSON.parse(bodyText);
    apiMessage = parsed?.error?.message || parsed?.message || '';
  } catch {
    apiMessage = String(bodyText || '').slice(0, 500);
  }
  const detail = redact(apiMessage, secret).slice(0, 600);

  // A rejected key arrives as HTTP 400 on `GET /models` and on a synthesis call,
  // not as 401, so it must be recognised from the message before the generic
  // 400 branch — otherwise the guidance blames the model id or the input text.
  const keyRejected = /API[_ ]key (?:not valid|expired|invalid)|API_KEY_INVALID|API_KEY_EXPIRED/i.test(apiMessage)
    || /API key not valid/i.test(bodyText);

  if (keyRejected) {
    return new GeminiError(`key rejected by Google (400): ${detail}`, {
      kind: 'api-key-invalid', status, stopRun: true,
      guidance: 'Google rejected the key itself (API_KEY_INVALID/API_KEY_EXPIRED), so no model id, voice or text will fix this. Re-copy the complete key from AI Studio into GEMINI_API_KEY or .env.local and re-run preflight. Preflight prints the resolved key length (never the key) — a short length means the paste was truncated.',
    });
  }
  if (status === 400) {
    return new GeminiError(`request rejected (400): ${detail}`, {
      kind: 'bad-request', status,
      guidance: 'Check the model id, voice name and input text; this request will not succeed unchanged.',
    });
  }
  if (status === 401) {
    return new GeminiError(`authentication failed (401): ${detail}`, {
      kind: 'auth', status, stopRun: true,
      guidance: 'GEMINI_API_KEY is missing, malformed or revoked. Supply a valid key and re-run.',
    });
  }
  if (status === 403) {
    return new GeminiError(`access denied (403): ${detail}`, {
      kind: 'permission', status, stopRun: true,
      guidance: 'The key lacks access to this model, or the Generative Language API / billing is not enabled for the project. Do not switch to a paid tier without owner approval.',
    });
  }
  if (status === 404) {
    return new GeminiError(`not found (404): ${detail}`, {
      kind: 'not-found', status, stopRun: true,
      guidance: 'Model or voice is not available to this key. Run preflight to list the models and voices the key can actually see.',
    });
  }
  if (status === 429) {
    return new GeminiError(`rate limited or quota exhausted (429): ${detail}`, {
      kind: 'quota', status, retryable: true, stopRun: true,
      guidance: 'Free-tier quota or rate limit reached. Stop generation, wait for the quota window to reset, then resume — do not enable billing without approval.',
    });
  }
  if (status >= 500) {
    return new GeminiError(`server error (${status}): ${detail}`, {
      kind: 'server', status, retryable: true,
      guidance: 'Transient Google-side failure; retrying is safe.',
    });
  }
  return new GeminiError(`unexpected HTTP ${status}: ${detail}`, { kind: 'unknown', status, detail });
}

/**
 * One HTTP call against the Generative Language API.
 *
 * @param {string} apiBase
 * @param {string} apiKey
 * @param {string} pathname
 * @param {{method?: string, body?: unknown, timeoutMs?: number}} [options]
 */
export async function callApi(apiBase, apiKey, pathname, options = {}) {
  const method = options.method || 'GET';
  const url = `${apiBase.replace(/\/+$/, '')}${pathname}`;
  const headers = { 'x-goog-api-key': apiKey, accept: 'application/json' };
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
    throw new GeminiError(redact(reason, apiKey), {
      kind: 'network', retryable: true, guidance: 'Check connectivity and retry.',
    });
  }

  const text = await response.text();
  if (!response.ok) throw classifyHttpError(response.status, text, apiKey);

  let json = null;
  if (text) {
    try {
      json = JSON.parse(text);
    } catch {
      throw new GeminiError('response was not valid JSON', { kind: 'protocol', status: response.status });
    }
  }
  return { status: response.status, json, text };
}

const AUDIO_MIME_RE = /^audio\//i;
const BASE64_RE = /^[A-Za-z0-9+/=\s]+$/;

/**
 * Find the audio payload in an interaction response.
 *
 * Checked in order, and the path that matched is returned with the payload so
 * the run log records how the contract was satisfied:
 *   1. `output_audio` (documented)
 *   2. `outputAudio`
 *   3. execution `steps` → content parts (`inline_data` / `inlineData`)
 *   4. a depth-limited scan for any `{data | bytes, mime_type | mimeType: audio/*}`
 *
 * @param {any} json
 * @returns {{data: string, mimeType: string, path: string}}
 */
export function extractAudio(json) {
  if (!json || typeof json !== 'object') {
    throw new GeminiError('response contained no JSON body', { kind: 'protocol' });
  }

  const direct = json.output_audio || json.outputAudio;
  if (direct && typeof direct === 'object' && typeof direct.data === 'string' && direct.data.length > 0) {
    return {
      data: direct.data,
      mimeType: direct.mime_type || direct.mimeType || 'audio/wav',
      path: json.output_audio ? 'output_audio.data' : 'outputAudio.data',
    };
  }

  const found = findAudioDeep(json, [], 0);
  if (found) return found;

  const status = json.status ? ` (status: ${json.status})` : '';
  throw new GeminiError(`no audio payload in response${status}`, {
    kind: 'protocol',
    guidance: 'The response shape did not match the documented contract; inspect the preserved response in .work/ and re-check the API reference.',
  });
}

function findAudioDeep(node, trail, depth) {
  if (!node || typeof node !== 'object' || depth > 8) return null;
  if (Array.isArray(node)) {
    for (let i = 0; i < node.length; i += 1) {
      const hit = findAudioDeep(node[i], trail.concat(String(i)), depth + 1);
      if (hit) return hit;
    }
    return null;
  }

  const mime = node.mime_type || node.mimeType || null;
  const data = typeof node.data === 'string' ? node.data : (typeof node.bytes === 'string' ? node.bytes : null);
  if (data && data.length > 64 && AUDIO_MIME_RE.test(String(mime || '')) && BASE64_RE.test(data.slice(0, 64))) {
    return { data, mimeType: String(mime), path: trail.join('.') || 'root' };
  }

  for (const [key, value] of Object.entries(node)) {
    const hit = findAudioDeep(value, trail.concat(key), depth + 1);
    if (hit) return hit;
  }
  return null;
}

/**
 * Build the interaction request body.
 *
 * With no style, `input` is the plain transcript string — the shape the docs
 * recommend testing first. With a style, the transcript is wrapped in a
 * `user_input` content part carrying a `speech_metadata` annotation, exactly as
 * the documented example does.
 *
 * @param {{model: string, text: string, voice: string, style?: string}} request
 */
export function buildInteractionBody(request) {
  const body = {
    model: request.model,
    input: request.style
      ? [{
          type: 'user_input',
          content: [{ type: 'text', text: request.text, annotations: [{ type: 'speech_metadata', style: request.style }] }],
        }]
      : request.text,
    response_format: { type: 'audio' },
    generation_config: { speech_config: [{ voice: request.voice }] },
    // Stateless: clinic announcement text is not retained server-side.
    store: false,
  };
  return body;
}

/**
 * Synthesise one transcript to audio.
 *
 * @param {object} options
 * @param {string} options.apiBase
 * @param {string} options.apiKey
 * @param {string} options.model
 * @param {string} options.voice
 * @param {string} options.text
 * @param {string} [options.style]
 * @param {number} [options.timeoutMs]
 * @returns {Promise<{buffer: Buffer, mimeType: string, responsePath: string, status: number}>}
 */
export async function synthesize(options) {
  const body = buildInteractionBody(options);
  const result = await callApi(options.apiBase, options.apiKey, INTERACTIONS_PATH, {
    method: 'POST',
    body,
    timeoutMs: options.timeoutMs,
  });

  const audio = extractAudio(result.json);
  const buffer = Buffer.from(audio.data, 'base64');
  if (buffer.length < 44) {
    throw new GeminiError(`decoded audio is only ${buffer.length} bytes`, {
      kind: 'protocol',
      guidance: 'The API returned a payload too small to be a WAV file; inspect the preserved response.',
    });
  }
  return { buffer, mimeType: audio.mimeType, responsePath: audio.path, status: result.status };
}

/**
 * List the models the key can see. Used by preflight to prove the configured
 * TTS model is actually available rather than assumed.
 *
 * @param {string} apiBase
 * @param {string} apiKey
 * @param {{pageSize?: number}} [options]
 */
export async function listModels(apiBase, apiKey, options = {}) {
  const pageSize = options.pageSize || 200;
  const collected = [];
  let pageToken = null;
  let pages = 0;

  do {
    const query = new URLSearchParams({ pageSize: String(pageSize) });
    if (pageToken) query.set('pageToken', pageToken);
    const { json } = await callApi(apiBase, apiKey, `/models?${query.toString()}`);
    const models = Array.isArray(json?.models) ? json.models : [];
    collected.push(...models);
    pageToken = json?.nextPageToken || null;
    pages += 1;
  } while (pageToken && pages < 10); // bounded: five pages covers this API comfortably

  return collected.map((model) => ({
    name: String(model.name || '').replace(/^models\//, ''),
    displayName: model.displayName || null,
    methods: Array.isArray(model.supportedGenerationMethods) ? model.supportedGenerationMethods : [],
  }));
}

/**
 * List voices available to the key (the Extended Voice Library plus prebuilt
 * voices). Only used to validate a configured voice name; the utility never
 * hardcodes the list.
 *
 * @param {string} apiBase
 * @param {string} apiKey
 */
export async function listVoices(apiBase, apiKey) {
  const { json } = await callApi(apiBase, apiKey, '/voices');
  const voices = Array.isArray(json?.voices) ? json.voices : [];
  return voices.map((voice) => ({
    name: String(voice.name || '').replace(/^voices\//, ''),
    languageCodes: Array.isArray(voice.languageCodes) ? voice.languageCodes : [],
    description: voice.description || null,
  }));
}

/** True when a model name is one of the documented TTS models. */
export function isTtsModelName(name) {
  return /-tts(\b|-)/.test(String(name || ''));
}
