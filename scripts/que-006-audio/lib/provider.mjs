/**
 * Provider selection and normalisation.
 *
 * `generate.mjs` and `preflight.mjs` should not care which service produced a
 * clip, so everything provider-specific lives here:
 *
 *   - which environment variables hold the key, model and voice;
 *   - how a request is shaped;
 *   - how a response becomes a **WAV buffer**, because the catalogue delivers
 *     `*.wav` and `validate.mjs` inspects WAV structure.
 *
 * Two providers are supported:
 *
 *   gemini      — Google Generative Language API; returns WAV natively.
 *   elevenlabs  — returns whatever `output_format` asks for. The default here is
 *                 `wav_24000`, which arrives as a complete WAV file, so the
 *                 normal path needs no decoder and no assumption about bit depth.
 *                 `pcm_*` is refused (headerless samples whose depth would have to
 *                 be assumed) and lossy containers are converted with ffmpeg.
 *
 * Nothing in this module asserts that a provider supports Bangla. That is
 * established only by a successful synthesis probe, whose result is recorded.
 */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { setting, PROVIDER_KEY_VARS } from './env.mjs';
import { TtsError } from './tts-error.mjs';
import { transcodeToWav } from './decode.mjs';
import * as gemini from './gemini-tts.mjs';
import * as elevenlabs from './elevenlabs-tts.mjs';

export { PROVIDER_KEY_VARS };

/** Providers this utility can drive, in the order `--help` lists them. */
export const PROVIDERS = ['gemini', 'elevenlabs'];

/** Human labels used in logs and the manifest. */
export const PROVIDER_LABELS = {
  gemini: 'Gemini TTS (Google Generative Language API)',
  elevenlabs: 'ElevenLabs TTS',
};

/** Where each provider's own documentation lives, quoted in `--help`. */
export const PROVIDER_DOCS = {
  gemini: 'https://ai.google.dev/gemini-api/docs/speech-generation',
  elevenlabs: 'https://elevenlabs.io/docs/api-reference/text-to-speech/convert',
};

/**
 * Resolve the provider name from an explicit flag, then the environment, then
 * the default. An unknown name is an error, never a silent fallback.
 *
 * @param {string|null} explicit
 * @returns {'gemini'|'elevenlabs'}
 */
export function resolveProviderName(explicit = null) {
  const name = (explicit || setting('QUE006_TTS_PROVIDER') || 'gemini').trim().toLowerCase();
  if (!PROVIDERS.includes(name)) {
    throw new Error(`unknown provider "${name}" (expected one of: ${PROVIDERS.join(', ')})`);
  }
  return /** @type {'gemini'|'elevenlabs'} */ (name);
}

/**
 * Build the generation configuration for one provider.
 *
 * CLI overrides win over environment variables, which win over documented
 * defaults. `voices` may be `null` for ElevenLabs: there is no correct default
 * voice id, and inventing one would generate the wrong voice silently, so the
 * run fails with an instruction instead.
 *
 * @param {'gemini'|'elevenlabs'} provider
 * @param {{model?: string|null, voiceEn?: string|null, voiceBn?: string|null,
 *   outputFormat?: string|null, apiBase?: string|null}} [overrides]
 */
export function resolveProviderConfig(provider, overrides = {}) {
  if (provider === 'elevenlabs') {
    const sharedVoice = setting('ELEVENLABS_VOICE_ID', null);
    return {
      provider,
      label: PROVIDER_LABELS.elevenlabs,
      apiBase: (overrides.apiBase || setting('ELEVENLABS_API_BASE') || elevenlabs.DEFAULT_API_BASE).replace(/\/+$/, ''),
      model: overrides.model || setting('ELEVENLABS_TTS_MODEL') || elevenlabs.DEFAULT_MODEL,
      voices: {
        en: overrides.voiceEn || setting('ELEVENLABS_VOICE_ID_EN', null) || sharedVoice,
        bn: overrides.voiceBn || setting('ELEVENLABS_VOICE_ID_BN', null) || sharedVoice,
      },
      // ElevenLabs has no speech-style string; delivery is a property of the
      // chosen voice plus optional voice_settings. Neither is invented here.
      styles: { en: null, bn: null },
      outputFormat: overrides.outputFormat || setting('ELEVENLABS_OUTPUT_FORMAT') || elevenlabs.DEFAULT_OUTPUT_FORMAT,
      voiceSettings: null,
      keyVars: PROVIDER_KEY_VARS.elevenlabs,
    };
  }

  return {
    provider: 'gemini',
    label: PROVIDER_LABELS.gemini,
    apiBase: (overrides.apiBase || setting('GEMINI_API_BASE') || gemini.DEFAULT_API_BASE).replace(/\/+$/, ''),
    model: overrides.model || setting('GEMINI_TTS_MODEL') || gemini.DEFAULT_MODEL,
    voices: {
      en: overrides.voiceEn || setting('GEMINI_VOICE_EN') || gemini.DEFAULT_VOICE,
      bn: overrides.voiceBn || setting('GEMINI_VOICE_BN') || gemini.DEFAULT_VOICE,
    },
    styles: {
      en: setting('GEMINI_TTS_STYLE_EN', null),
      bn: setting('GEMINI_TTS_STYLE_BN', null),
    },
    outputFormat: null,
    voiceSettings: null,
    keyVars: PROVIDER_KEY_VARS.gemini,
  };
}

/** True when a buffer starts with a RIFF/WAVE header. */
function isRiffWav(buffer) {
  return Boolean(buffer) && buffer.length >= 12
    && buffer.toString('ascii', 0, 4) === 'RIFF'
    && buffer.toString('ascii', 8, 12) === 'WAVE';
}

/** File extension for a lossy container, used only for the transcode temp file. */
function extensionForFamily(family) {
  switch (family) {
    case 'mp3': return 'mp3';
    case 'opus': return 'ogg';
    case 'ulaw': return 'ulaw';
    case 'alaw': return 'alaw';
    default: return 'bin';
  }
}

/**
 * Synthesise one clip and return a buffer that is **always a WAV file**.
 *
 * That single guarantee is what lets the rest of the pipeline stay unchanged:
 * the delivery file, the preserved master and `validate.mjs` all expect WAV.
 *
 * @param {object} config as returned by {@link resolveProviderConfig}
 * @param {{apiKey: string, voice: string, text: string, style?: string|null,
 *   timeoutMs?: number}} request
 * @returns {Promise<{buffer: Buffer, mimeType: string, responsePath: string,
 *   status: number, meta: {provider: string, requestedFormat: string,
 *   deliveredFormat: string, transcode: string}}>}
 */
export async function synthesizeWav(config, request) {
  const { apiKey, voice, text, style, timeoutMs } = request;

  if (config.provider === 'elevenlabs') {
    const family = elevenlabs.formatFamily(config.outputFormat);
    if (family === 'pcm') {
      // Headerless samples: the bit depth is not stated in the payload, and a
      // wrongly declared header would produce a file that plays at the wrong
      // speed. Refuse rather than assume.
      throw new TtsError(`output_format "${config.outputFormat}" returns headerless samples`, {
        kind: 'config', provider: 'elevenlabs', stopRun: true,
        guidance: 'Use a wav_* format (default wav_24000) so the response carries its own '
          + 'sample rate and bit depth, or an mp3_*/opus_* format that ffmpeg can convert.',
      });
    }

    const audio = await elevenlabs.synthesize({
      apiBase: config.apiBase,
      apiKey,
      model: config.model,
      voice,
      text,
      outputFormat: config.outputFormat,
      voiceSettings: config.voiceSettings,
      timeoutMs,
    });

    if (isRiffWav(audio.buffer)) {
      return {
        buffer: audio.buffer,
        mimeType: 'audio/wav',
        responsePath: `${audio.responsePath} -> RIFF/WAVE body`,
        status: audio.status,
        meta: {
          provider: 'elevenlabs',
          requestedFormat: config.outputFormat,
          deliveredFormat: `${config.outputFormat} (WAV container as returned)`,
          transcode: 'none',
        },
      };
    }

    if (family === 'wav') {
      const head = audio.buffer.subarray(0, 16).toString('hex');
      throw new TtsError(`asked for ${config.outputFormat} but the body is not RIFF/WAVE`, {
        kind: 'protocol', provider: 'elevenlabs', status: audio.status,
        guidance: `The response did not start with a RIFF header (first bytes: ${head}). `
          + 'The contract changed or a proxy altered the body; nothing was written.',
      });
    }

    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'amsdp-que006-'));
    try {
      const inputPath = path.join(tempDir, `response.${extensionForFamily(family)}`);
      const outputPath = path.join(tempDir, 'converted.wav');
      fs.writeFileSync(inputPath, audio.buffer);
      const converted = transcodeToWav(inputPath, outputPath, { channels: 1 });
      if (!converted.ok) {
        throw new TtsError(`could not convert ${config.outputFormat} to WAV: ${converted.detail}`, {
          kind: 'transcode', provider: 'elevenlabs', stopRun: true,
          guidance: 'Install ffmpeg, or set ELEVENLABS_OUTPUT_FORMAT to a wav_* value so no conversion is needed.',
        });
      }
      const buffer = fs.readFileSync(outputPath);
      return {
        buffer,
        mimeType: 'audio/wav',
        responsePath: `${audio.responsePath} -> ffmpeg ${family}->wav`,
        status: audio.status,
        meta: {
          provider: 'elevenlabs',
          requestedFormat: config.outputFormat,
          deliveredFormat: `${config.outputFormat} converted to PCM WAV`,
          transcode: converted.detail,
        },
      };
    } finally {
      try { fs.rmSync(tempDir, { recursive: true, force: true }); } catch { /* temp cleanup is best effort */ }
    }
  }

  const audio = await gemini.synthesize({
    apiBase: config.apiBase,
    apiKey,
    model: config.model,
    voice,
    text,
    style,
    timeoutMs,
  });
  return {
    buffer: audio.buffer,
    mimeType: audio.mimeType,
    responsePath: audio.responsePath,
    status: audio.status,
    meta: {
      provider: 'gemini',
      requestedFormat: 'audio/wav (native)',
      deliveredFormat: audio.mimeType,
      transcode: 'none',
    },
  };
}
/**
 * The shortest text that still exercises synthesis, per language.
 *
 * Used only by the preflight probe: it proves audio comes back for that voice and
 * script without spending meaningful quota on the account.
 */
export function probeTextFor(language) {
  return language === 'bn' ? 'টোকেন' : 'ok';
}

/**
 * List the models the configured key can see, normalised across providers.
 *
 * @param {object} config
 * @param {string} apiKey
 * @returns {Promise<Array<{id: string, name: string|null, canSpeak: boolean, languages: string[]}>>}
 */
export async function listModelsFor(config, apiKey) {
  if (config.provider === 'elevenlabs') {
    const models = await elevenlabs.listModels(config.apiBase, apiKey);
    return models.map((model) => ({
      id: model.modelId,
      name: model.name,
      canSpeak: model.canDoTextToSpeech,
      languages: model.languages,
    }));
  }
  const models = await gemini.listModels(config.apiBase, apiKey);
  return models.map((model) => ({
    id: model.name,
    name: model.displayName,
    canSpeak: model.methods.includes('generateContent') || gemini.isTtsModelName(model.name),
    languages: [],
  }));
}

/**
 * List the voices the configured key can use, normalised across providers.
 *
 * The `language`/`accent` fields come from the provider's own labels, so a Bangla
 * voice is chosen from reported data rather than guessed at.
 *
 * @param {object} config
 * @param {string} apiKey
 * @returns {Promise<Array<{id: string, name: string|null, category: string|null,
 *   language: string|null, accent: string|null, description: string|null}>>}
 */
export async function listVoicesFor(config, apiKey) {
  if (config.provider === 'elevenlabs') {
    const voices = await elevenlabs.listVoices(config.apiBase, apiKey);
    return voices.map((voice) => ({
      id: voice.voiceId,
      name: voice.name,
      category: voice.category,
      language: voice.labels.language || null,
      accent: voice.labels.accent || null,
      description: voice.description,
    }));
  }
  const voices = await gemini.listVoices(config.apiBase, apiKey);
  return voices.map((voice) => ({
    id: voice.name,
    name: voice.name,
    category: 'prebuilt',
    language: voice.languageCodes.length ? voice.languageCodes.join(',') : null,
    accent: null,
    description: voice.description,
  }));
}

/**
 * Render one voice per line, id first, so a value can be copied straight into
 * `ELEVENLABS_VOICE_ID_EN` / `..._BN` or `GEMINI_VOICE_EN` / `..._BN`.
 *
 * @param {Array<{id: string, name: string|null, category: string|null,
 *   language: string|null, accent: string|null}>} voices
 */
export function formatVoiceTable(voices) {
  const lines = [];
  const idWidth = Math.min(40, Math.max(8, ...voices.map((voice) => voice.id.length)));
  for (const voice of voices) {
    const meta = [voice.language, voice.accent, voice.category].filter(Boolean).join(' · ');
    lines.push(`  ${voice.id.padEnd(idWidth)}  ${(voice.name || '').padEnd(22)}  ${meta}`);
  }
  return lines;
}

/**
 * The instructions a human needs when no key resolved, worded for the provider so
 * the wrong variable name is never suggested.
 *
 * @param {object} config
 * @param {{source: string}} resolution result of `resolveApiKey`
 * @param {string[]} [extras] caller-specific lines, inserted before the closing note
 */
export function missingKeyGuidance(config, resolution, extras = []) {
  const vars = config.keyVars;
  const primary = vars[0];
  const lines = [
    `ERROR ${primary} is not set, and at least one selected asset needs speech generation.`,
    `  Provider: ${config.label}.`,
    `  Set it for this shell:  $env:${primary} = "..."        (PowerShell)`,
    '  or write it once to     .env.local at the repository root (git-ignored)',
  ];
  if (vars.length > 1) {
    lines.push(`  Also accepted: ${vars.slice(1).join(', ')}.`);
  }
  lines.push(`  Looked in: ${resolution.source}. Order: process environment, .env.local, .env.`);
  for (const extra of extras) lines.push(extra);
  lines.push('Nothing was generated, no file was written, and manifest.json was not modified.');
  return lines;
}


