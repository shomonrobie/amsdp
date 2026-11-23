/**
 * Environment and secret handling for the QUE-006 audio utility.
 *
 * The API key is only ever read into memory and sent as a request header. It is
 * never printed, never written to the manifest, the state file or the run log,
 * and every string this utility prints passes through `redact()` first so an
 * error message that echoes a key cannot leak it.
 *
 * Lookup order for the key of the selected provider:
 *   1. the process environment (the documented path);
 *   2. a git-ignored `.env.local` then `.env` at the repository root, for
 *      convenience so the key need not be pasted into a shell each session.
 *
 * Supported providers, and the variable each one uses:
 *   - `gemini`     → `GEMINI_API_KEY`
 *   - `elevenlabs` → `ELEVEN_LABS_API_KEY`, or `ELEVENLABS_API_KEY` (both are
 *                    accepted because both spellings are in circulation)
 *
 * No other variable is read from those files, and their contents are never
 * echoed — only the file name that supplied the key is reported.
 */

import fs from 'node:fs';
import path from 'node:path';
import { REPO_ROOT } from './paths.mjs';

/** Environment files consulted, in order, when the variable is not exported. */
export const ENV_FILE_CANDIDATES = ['.env.local', '.env'];

/**
 * Variable names accepted per provider, in priority order.
 *
 * `elevenlabs` accepts both spellings: the task that commissioned this utility
 * used `ELEVEN_LABS_API_KEY`, while ElevenLabs' own documentation uses
 * `ELEVENLABS_API_KEY`. Reading both means a key placed under either name works,
 * and the reported source names the variable that actually matched.
 */
export const PROVIDER_KEY_VARS = {
  gemini: ['GEMINI_API_KEY'],
  elevenlabs: ['ELEVEN_LABS_API_KEY', 'ELEVENLABS_API_KEY'],
};

/** Providers this utility can talk to. */
export const PROVIDERS = Object.keys(PROVIDER_KEY_VARS);


/**
 * Parse a dotenv-style file. Deliberately minimal: `KEY=value`, optional
 * surrounding quotes, `#` comments, `export ` prefix tolerated.
 *
 * @param {string} filePath
 * @returns {Record<string, string>}
 */
export function parseEnvFile(filePath) {
  const text = fs.readFileSync(filePath, 'utf8');
  const out = {};
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const match = /^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/.exec(line);
    if (!match) continue;
    let value = match[2].trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    out[match[1]] = value;
  }
  return out;
}

/**
 * Resolve the API key for a provider without ever exposing it.
 *
 * Precedence is the documented order (environment first, then `.env.local`,
 * then `.env`), with one deliberate exception: a value that **cannot be a real
 * key** — too short, or the wrong prefix — never shadows a value that can.
 *
 * That exception is not theoretical. A stale `ELEVEN_LABS_API_KEY=sk_xxx` left in
 * one shell silently overrode a complete 51-character key in `.env.local`, and the
 * only symptom was a `401 invalid_api_key` that sent the reader off to re-copy a
 * key that was already correct. Whenever a candidate is skipped for this reason it
 * is reported in `ignored`, so nothing is overridden silently.
 *
 * @param {string} [provider] one of {@link PROVIDERS}
 * @returns {{key: string|null, source: string, variable: string|null, provider: string,
 *   ignored: {source: string, variable: string, length: number}[]}}
 */
export function resolveApiKey(provider = 'gemini') {
  const vars = PROVIDER_KEY_VARS[provider];
  if (!vars) throw new Error(`unknown provider: ${provider}`);

  /** @type {{key: string, source: string, variable: string}[]} */
  const candidates = [];
  for (const name of vars) {
    const fromProcess = process.env[name];
    if (fromProcess && fromProcess.trim()) {
      candidates.push({ key: fromProcess.trim(), source: `environment variable ${name}`, variable: name });
    }
  }

  for (const file of ENV_FILE_CANDIDATES) {
    const candidatePath = path.join(REPO_ROOT, file);
    if (!fs.existsSync(candidatePath)) continue;
    let parsed;
    try {
      parsed = parseEnvFile(candidatePath);
    } catch {
      continue;
    }
    for (const name of vars) {
      if (parsed[name] && parsed[name].trim()) {
        candidates.push({ key: parsed[name].trim(), source: `${file} (repository root)`, variable: name });
      }
    }
  }

  if (candidates.length === 0) {
    return { key: null, source: 'not found', variable: null, provider, ignored: [] };
  }

  const chosen = candidates.find((entry) => describeKeyShape(entry.key, provider).looksStandard) || candidates[0];
  const chosenIndex = candidates.indexOf(chosen);
  const ignored = candidates
    .slice(0, chosenIndex)
    .filter((entry) => !describeKeyShape(entry.key, provider).looksStandard)
    .map((entry) => ({ source: entry.source, variable: entry.variable, length: entry.key.length }));

  return { key: chosen.key, source: chosen.source, variable: chosen.variable, provider, ignored };
}

/** Shortest value this utility will treat as a plausible ElevenLabs key. */
const ELEVENLABS_MIN_PLAUSIBLE_LENGTH = 32;

/**
 * Describe the *shape* of a resolved key so a bad paste is diagnosable without
 * revealing the value.
 *
 * Google AI Studio: 39 characters beginning `AIza`. ElevenLabs: begins `sk_` and
 * is much longer than a placeholder. Only the length and boolean character-class
 * facts are reported, never the key itself. This matters because a key whose tail
 * was lost still *resolves*: Google answers it with HTTP 400 `API key not valid`
 * and ElevenLabs with HTTP 401, and both errors read like a model, voice or text
 * problem, sending people looking in the wrong place.
 *
 * @param {string|null} key
 * @param {string} [provider]
 * @returns {{present: boolean, provider: string, length: number,
 *   standardPrefix: boolean, standardLength: boolean, safeCharsOnly: boolean,
 *   looksStandard: boolean, detail: string}}
 */
export function describeKeyShape(key, provider = 'gemini') {
  const presentFields = { provider, length: key ? key.length : 0 };
  if (!key) {
    return {
      present: false,
      ...presentFields,
      standardPrefix: false,
      standardLength: false,
      safeCharsOnly: false,
      looksStandard: false,
      detail: 'no key resolved',
    };
  }

  const length = key.length;
  // Both key formats are base64url-ish; the pattern is a paste sanity check only.
  const safeCharsOnly = /^[A-Za-z0-9_-]+$/.test(key);

  if (provider === 'elevenlabs') {
    const standardPrefix = key.startsWith('sk_');
    const standardLength = length >= ELEVENLABS_MIN_PLAUSIBLE_LENGTH;
    const looksStandard = standardPrefix && standardLength && safeCharsOnly;
    const detail = looksStandard
      ? `${length}-character key, standard ElevenLabs shape`
      : `${length}-character key; an ElevenLabs key starts "sk_" followed by a long token `
        + `(prefix ${standardPrefix ? 'as expected' : 'unexpected'}, length ${standardLength ? 'as expected' : 'unusual'}) `
        + '— a truncated paste, or the placeholder "sk_xxx" itself, is the usual cause';
    return { present: true, ...presentFields, standardPrefix, standardLength, safeCharsOnly, looksStandard, detail };
  }

  const EXPECTED_LENGTH = 39;
  const standardPrefix = key.startsWith('AIza');
  const standardLength = length === EXPECTED_LENGTH;
  const looksStandard = standardPrefix && standardLength && safeCharsOnly;
  const detail = looksStandard
    ? `${length}-character key, standard AI Studio shape`
    : `${length}-character key; an AI Studio key is ${EXPECTED_LENGTH} characters and starts "AIza" `
      + `(prefix ${standardPrefix ? 'as expected' : 'unexpected'}, length ${standardLength ? 'as expected' : 'unusual'}) `
      + '— a truncated or partial paste is the usual cause';
  return { present: true, ...presentFields, standardPrefix, standardLength, safeCharsOnly, looksStandard, detail };
}


/** Read a plain setting from the environment with a fallback. */
export function setting(name, fallback) {
  const value = process.env[name];
  return value && value.trim() ? value.trim() : fallback;
}

/**
 * Remove any secret from text before it is printed or persisted.
 *
 * Three layers: an exact match on the live key, a pattern match on the shapes
 * provider keys take (`AIza…` for Google, `sk_…` for ElevenLabs), and a match on
 * the header/query parameter that carries a key in case a key this process does
 * not know about still appears in an error body.
 *
 * The `sk_` pattern deliberately requires a long token after the prefix so the
 * placeholder `sk_xxx` a person might type stays readable in a diagnostic.
 *
 * @param {unknown} value
 * @param {string|null} [secret]
 */
export function redact(value, secret = null) {
  let text = typeof value === 'string' ? value : JSON.stringify(value);
  if (text == null) return '';
  if (secret && secret.length >= 8) {
    text = text.split(secret).join('[REDACTED]');
  }
  text = text.replace(/AIza[0-9A-Za-z\-_]{10,}/g, '[REDACTED]');
  text = text.replace(/sk_[0-9A-Za-z\-_]{16,}/g, '[REDACTED]');
  text = text.replace(/([?&](?:key|api_key|apikey)=)[^&\s"']+/gi, '$1[REDACTED]');
  text = text.replace(/(x-goog-api-key["'\s:]+)[^\s"',}]+/gi, '$1[REDACTED]');
  text = text.replace(/(xi-api-key["'\s:]+)[^\s"',}]+/gi, '$1[REDACTED]');
  return text;
}
