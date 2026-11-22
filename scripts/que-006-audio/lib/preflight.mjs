/**
 * Preflight checks for the QUE-006 audio utility.
 *
 * Purpose: find out whether the key, the model and the voice actually work
 * **before** spending quota on 28 assets, and fail with a specific, actionable
 * message instead of a generic HTTP error.
 *
 * Two providers are supported; `runPreflight` dispatches on `options.provider`
 * and the Gemini path is unchanged:
 *
 *   gemini      — key → GET /models → GET /voices → one synthesis probe
 *   elevenlabs  — key → GET /models → GET /voices → one probe **per configured
 *                 voice**, so both the English and the Bangla clip are proven to
 *                 come back as usable audio before a 28-asset run is started.
 *
 * The ElevenLabs probe goes through `provider.synthesizeWav`, i.e. exactly the
 * conversion the real run uses, so a format that cannot be turned into a WAV
 * fails here rather than on asset 19 of 27.
 *
 * The probe is skipped with `--no-probe`. A pass on the probe is the only thing
 * that proves speech access; the listing checks only prove visibility.
 */

import { synthesize, listModels, listVoices, isTtsModelName, GeminiError } from './gemini-tts.mjs';
import {
  listModels as elevenModels,
  listVoices as elevenVoices,
  isTtsModelName as isElevenModelName,
} from './elevenlabs-tts.mjs';
import { synthesizeWav, probeTextFor } from './provider.mjs';
import { TtsError } from './tts-error.mjs';
import { inspectAudioFile } from './audio-file.mjs';
import { redact, describeKeyShape } from './env.mjs';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

/**
 * @param {object} options
 * @param {string} [options.provider] 'gemini' (default) or 'elevenlabs'
 * @param {string} options.apiBase
 * @param {string} options.apiKey
 * @param {string} options.model
 * @param {string[]} options.voices
 * @param {string} [options.outputFormat] ElevenLabs `output_format`
 * @param {boolean} [options.probe]
 */
export async function runPreflight(options) {
  if ((options.provider || 'gemini') === 'elevenlabs') return runElevenLabsPreflight(options);
  return runGeminiPreflight(options);
}

/**
 * @param {object} options
 */
async function runGeminiPreflight(options) {

  const checks = [];
  const failures = [];
  const warnings = [];
  const apiKey = options.apiKey;

  // --- 1. key -------------------------------------------------------------
  // The value is never printed. Its *shape* is, because a truncated paste is
  // rejected by Google with a 400 that blames nothing in particular.
  const keyShape = describeKeyShape(apiKey);
  if (keyShape.looksStandard) {
    checks.push({ name: 'api-key', status: 'pass', detail: `GEMINI_API_KEY resolved — ${keyShape.detail}` });
  } else {
    checks.push({ name: 'api-key', status: 'warn', detail: `GEMINI_API_KEY resolved — ${keyShape.detail}` });
    warnings.push(
      `The resolved key does not have the standard AI Studio shape: ${keyShape.detail}. `
      + 'If preflight reports API_KEY_INVALID below, this is the cause — re-copy the whole key.',
    );
  }

  // --- 2. models ----------------------------------------------------------
  let models = [];
  const ttsModels = [];
  try {
    models = await listModels(options.apiBase, apiKey);
    for (const entry of models) if (isTtsModelName(entry.name)) ttsModels.push(entry.name);
    const found = models.some((entry) => entry.name === options.model);
    if (found) {
      checks.push({ name: 'model-visible', status: 'pass', detail: `"${options.model}" is listed for this key` });
    } else {
      checks.push({ name: 'model-visible', status: 'fail', detail: `"${options.model}" is not listed for this key` });
      failures.push(
        `Configured model "${options.model}" is not available to this key. `
        + `TTS models this key can see: ${ttsModels.length ? ttsModels.join(', ') : 'none'}. `
        + 'Set GEMINI_TTS_MODEL to one of those, or check that the project has the Generative Language API enabled.',
      );
    }
  } catch (err) {
    const message = err instanceof GeminiError ? `${err.kind}: ${err.message}` : String(err?.message || err);
    checks.push({ name: 'model-visible', status: 'fail', detail: redact(message, apiKey) });
    failures.push(`GET /models failed (${err?.kind || 'error'}). ${err?.guidance || ''}`.trim());
  }

  // --- 3. voices ----------------------------------------------------------
  try {
    const voices = await listVoices(options.apiBase, apiKey);
    const names = new Set(voices.map((voice) => voice.name));
    for (const voice of options.voices) {
      if (names.has(voice)) {
        checks.push({ name: `voice-${voice}`, status: 'pass', detail: `"${voice}" is listed by GET /voices` });
      } else {
        checks.push({ name: `voice-${voice}`, status: 'warn', detail: `"${voice}" is not listed by GET /voices` });
        warnings.push(
          `Voice "${voice}" was not returned by GET /voices (${names.size} voices listed). `
          + 'The probe below decides whether it is usable; if it fails, set GEMINI_VOICE_EN / GEMINI_VOICE_BN to a listed voice.',
        );
      }
    }
  } catch (err) {
    const message = err instanceof GeminiError ? `${err.kind}: ${err.message}` : String(err?.message || err);
    checks.push({ name: 'voice-list', status: 'warn', detail: redact(message, apiKey) });
    warnings.push('GET /voices is unavailable for this key; voice names are validated by the probe instead.');
  }

  // --- 4. probe -----------------------------------------------------------
  if (options.probe !== false) {
    const probePath = path.join(os.tmpdir(), `amsdp-que006-probe-${process.pid}.wav`);
    try {
      const audio = await synthesize({
        apiBase: options.apiBase,
        apiKey,
        model: options.model,
        voice: options.voices[0],
        text: 'ok',
      });
      fs.writeFileSync(probePath, audio.buffer);
      const record = inspectAudioFile(probePath);
      if (record.decodable && record.durationMs > 0 && !record.silent) {
        checks.push({
          name: 'synthesis-probe',
          status: 'pass',
          detail: `audio returned via ${audio.responsePath}, ${record.mimeType}, ${record.durationMs} ms, ${record.sha256?.slice(0, 12)}…`,
        });
      } else {
        checks.push({ name: 'synthesis-probe', status: 'fail', detail: `unusable audio: ${record.problems.join('; ') || 'silent or zero-length'}` });
        failures.push('The synthesis probe returned audio that could not be validated; do not start batch generation.');
      }
    } catch (err) {
      const message = err instanceof GeminiError ? `${err.kind}: ${err.message}` : String(err?.message || err);
      checks.push({ name: 'synthesis-probe', status: 'fail', detail: redact(message, apiKey) });
      failures.push(`Synthesis probe failed (${err?.kind || 'error'}). ${err?.guidance || ''}`.trim());
    } finally {
      try { fs.rmSync(probePath, { force: true }); } catch { /* probe cleanup is best effort */ }
    }
  } else {
    checks.push({ name: 'synthesis-probe', status: 'skipped', detail: 'skipped by --no-probe' });
    warnings.push('Synthesis probe skipped: model visibility alone does not prove that speech generation works.');
  }

  return { ok: failures.length === 0, checks, failures, warnings, ttsModels };
}

/**
 * ElevenLabs preflight.
 *
 * Differs from the Gemini path in one deliberate way: the probe runs once per
 * configured voice (English and Bangla), because a voice that works for English
 * proves nothing about the Bangla clip — and the Bangla clip is the one a native
 * speaker must later review. Each probe goes through `synthesizeWav`, so the
 * output format is proven convertible before the batch starts.
 *
 * @param {object} options
 */
async function runElevenLabsPreflight(options) {
  const checks = [];
  const failures = [];
  const warnings = [];
  const apiKey = options.apiKey;
  const voiceTargets = Array.isArray(options.voiceTargets) && options.voiceTargets.length
    ? options.voiceTargets
    : [{ language: 'en', voice: options.voices[0] || null }];

  // --- 1. key -------------------------------------------------------------
  // The value is never printed; its shape is, because a rejected ElevenLabs key
  // is a 401 that says nothing about which variable held it.
  const keyShape = describeKeyShape(apiKey, 'elevenlabs');
  if (keyShape.looksStandard) {
    checks.push({ name: 'api-key', status: 'pass', detail: `ELEVEN_LABS_API_KEY resolved — ${keyShape.detail}` });
  } else {
    checks.push({ name: 'api-key', status: 'warn', detail: `ELEVEN_LABS_API_KEY resolved — ${keyShape.detail}` });
    warnings.push(
      `The resolved key does not have the expected ElevenLabs shape: ${keyShape.detail}. `
      + 'If the probe below reports api-key-invalid, this is the cause — re-copy the whole key.',
    );
  }

  // --- 2. models ----------------------------------------------------------
  const ttsModels = [];
  try {
    const models = await elevenModels(options.apiBase, apiKey);
    for (const model of models) {
      if (model.canDoTextToSpeech || isElevenModelName(model.modelId)) ttsModels.push(model.modelId);
    }
    const configured = models.find((model) => model.modelId === options.model);
    if (!configured) {
      checks.push({ name: 'model-visible', status: 'fail', detail: `"${options.model}" is not listed for this key` });
      failures.push(
        `Configured model "${options.model}" is not available to this key. `
        + `TTS models this key can see: ${ttsModels.length ? ttsModels.join(', ') : 'none'}. `
        + 'Set ELEVENLABS_TTS_MODEL to one of those.',
      );
    } else if (!configured.canDoTextToSpeech) {
      checks.push({ name: 'model-visible', status: 'fail', detail: `"${options.model}" is listed but cannot do text to speech` });
      failures.push('"' + options.model + '" reports can_do_text_to_speech=false; choose a speech model (e.g. eleven_multilingual_v2).');
    } else {
      checks.push({ name: 'model-visible', status: 'pass', detail: `"${options.model}" is listed and can do text to speech` });
    }
  } catch (err) {
    const message = err instanceof TtsError ? `${err.kind}: ${err.message}` : String(err?.message || err);
    // A key scoped for synthesis but not for listing is a *legitimate*
    // least-privilege configuration: it can generate audio even though it cannot
    // enumerate models. That is a warning, not a failure — the probe below is the
    // real test. A rejected key stays a failure.
    if (err?.kind === 'key-permissions') {
      checks.push({ name: 'model-visible', status: 'warn', detail: redact(message, apiKey) });
      warnings.push(
        `The key cannot list models, so the configured model "${options.model}" is used unverified. `
        + 'That is acceptable for a synthesis-only key: the probe below is the real test.',
      );
    } else {
      checks.push({ name: 'model-visible', status: 'fail', detail: redact(message, apiKey) });
      failures.push(`GET /models failed (${err?.kind || 'error'}). ${err?.guidance || ''}`.trim());
    }
  }

  // --- 3. voices ----------------------------------------------------------
  const configuredVoices = Array.from(new Set(voiceTargets.map((target) => target.voice).filter(Boolean)));
  if (configuredVoices.length === 0) {
    checks.push({ name: 'voice-configured', status: 'fail', detail: 'no voice id configured' });
    failures.push(
      'No ElevenLabs voice id is configured. Run --list-voices to see the ids this account can use, then set '
      + 'ELEVENLABS_VOICE_ID_EN and ELEVENLABS_VOICE_ID_BN (or a single ELEVENLABS_VOICE_ID for both languages).',
    );
  }

  try {
    const listed = await elevenVoices(options.apiBase, apiKey);
    const byId = new Map(listed.map((voice) => [voice.voiceId, voice]));
    const missing = [];
    for (const voiceId of configuredVoices) {
      const found = byId.get(voiceId);
      if (found) {
        const meta = [found.labels.language, found.labels.accent, found.category].filter(Boolean).join(' · ');
        checks.push({
          name: `voice-${found.name || voiceId}`,
          status: 'pass',
          detail: `"${voiceId}" is listed${meta ? ` (${meta})` : ''}`,
        });
      } else {
        missing.push(voiceId);
        checks.push({ name: `voice-${voiceId}`, status: 'fail', detail: `"${voiceId}" is not listed by GET /voices (${listed.length} voices)` });
      }
    }
    if (missing.length) {
      failures.push(
        `Voice id(s) not listed for this account: ${missing.join(', ')}. `
        + 'Run --list-voices to see the ids that are; do not guess an id.',
      );
    }
  } catch (err) {
    const message = err instanceof TtsError ? `${err.kind}: ${err.message}` : String(err?.message || err);
    checks.push({ name: 'voice-list', status: 'warn', detail: redact(message, apiKey) });
    warnings.push('GET /voices is unavailable for this key; voice ids are validated by the probes instead.');
  }

  // --- 4. probes, one per configured voice --------------------------------
  // A rejected key makes every later check meaningless and every probe would be
  // a pointless request: stop here and say so once. A key that is valid but
  // unscoped (`key-permissions`) behaves the same way — the probe would fail for
  // the same reason — so it short-circuits too, with its own wording.
  const blocking = checks.find((check) => check.status === 'fail' && /api-key-invalid|key-permissions/.test(String(check.detail || '')));
  if (blocking) {
    const permissionsOnly = !checks.some((check) => String(check.detail || '').includes('api-key-invalid'));
    checks.push({
      name: 'synthesis-probe',
      status: 'skipped',
      detail: permissionsOnly
        ? 'skipped: the key is not scoped for this call'
        : 'skipped: the key was rejected',
    });
    warnings.push(permissionsOnly
      ? 'Synthesis probes skipped because the key lacks the required scope; add the scope and re-run.'
      : 'Synthesis probes skipped because the key itself was rejected; fix the key first.');
    return { ok: false, checks, failures, warnings, ttsModels };
  }
  if (options.probe === false) {
    checks.push({ name: 'synthesis-probe', status: 'skipped', detail: 'skipped by --no-probe' });
    warnings.push('Synthesis probes skipped: model and voice listing alone does not prove that speech generation works.');
    return { ok: failures.length === 0, checks, failures, warnings, ttsModels };
  }

  const targets = [];
  for (const target of voiceTargets) {
    if (!target.voice) continue;
    if (targets.some((entry) => entry.language === target.language && entry.voice === target.voice)) continue;
    targets.push(target);
  }

  for (const target of targets) {
    const name = `probe-${target.language}`;
    const probePath = path.join(os.tmpdir(), `amsdp-que006-probe-${target.language}-${process.pid}.wav`);
    const probeConfig = {
      provider: 'elevenlabs',
      apiBase: options.apiBase,
      model: options.model,
      voices: { en: target.voice, bn: target.voice },
      styles: { en: null, bn: null },
      outputFormat: options.outputFormat,
      voiceSettings: null,
      keyVars: ['ELEVEN_LABS_API_KEY', 'ELEVENLABS_API_KEY'],
    };
    try {
      const audio = await synthesizeWav(probeConfig, {
        apiKey,
        voice: target.voice,
        text: probeTextFor(target.language),
      });
      fs.writeFileSync(probePath, audio.buffer);
      const record = inspectAudioFile(probePath);
      if (record.decodable && record.durationMs > 0 && !record.silent) {
        checks.push({
          name,
          status: 'pass',
          detail: `${target.language} audio returned (${audio.meta.deliveredFormat}), ${record.mimeType || 'wav'}, `
            + `${record.durationMs} ms, ${record.sha256?.slice(0, 12)}…`,
        });
      } else {
        checks.push({
          name,
          status: 'fail',
          detail: `unusable audio: ${record.problems.join('; ') || 'silent or zero-length'}`,
        });
        failures.push(`The ${target.language} probe returned audio that could not be validated; do not start batch generation.`);
      }
    } catch (err) {
      const message = err instanceof TtsError ? `${err.kind}: ${err.message}` : String(err?.message || err);
      checks.push({ name, status: 'fail', detail: redact(message, apiKey) });
      failures.push(`${target.language} synthesis probe failed (${err?.kind || 'error'}). ${err?.guidance || ''}`.trim());
    } finally {
      try { fs.rmSync(probePath, { force: true }); } catch { /* probe cleanup is best effort */ }
    }
  }

  return { ok: failures.length === 0, checks, failures, warnings, ttsModels };
}

