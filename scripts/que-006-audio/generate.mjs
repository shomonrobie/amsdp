#!/usr/bin/env node
/**
 * QUE-006 — generate the 28 catalogue recordings with Gemini TTS.
 *
 *   node scripts/que-006-audio/generate.mjs --all
 *   node scripts/que-006-audio/generate.mjs --smoke
 *   node scripts/que-006-audio/generate.mjs --en | --bn
 *   node scripts/que-006-audio/generate.mjs --asset en.digit.4,bn.digit.4
 *   node scripts/que-006-audio/generate.mjs --rebuild-manifest
 *   node scripts/que-006-audio/generate.mjs --check-catalogue
 *
 * Behaviour that matters:
 *   - Resumable: an asset with a valid, already-generated file is skipped unless
 *     --force is given, so a quota interruption costs nothing to continue.
 *   - Fail-fast on failures that cannot fix themselves (bad key, no access,
 *     quota exhausted, missing model): the run stops and reports rather than
 *     hammering the API 28 times.
 *   - Never prints, logs or persists the API key.
 *   - Never claims more than the files prove: the manifest is rebuilt from disk
 *     after every run, and a file that failed validation is not left behind in
 *     `frontend/public/audio/`.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  ASSETS,
  ASSET_BY_ID,
  ASSET_IDS,
  CATALOGUE_ASSET_COUNT,
  PUNCTUATION_PAUSE_MS,
  SPOKEN_TEXT_OVERRIDES,
  recordedTextFor,
  diffAgainstDoc,
  diffComposedAgainstApproved,
} from './catalogue.mjs';
import {
  AUDIO_ROOT,
  MANIFEST_PATH,
  STATE_PATH,
  LAST_RUN_PATH,
  REPO_ROOT,
  audioPathFor,
  masterPathFor,
} from './lib/paths.mjs';
import { resolveApiKey, redact } from './lib/env.mjs';
import { inspectAudioFile, writeSilentWav, describeAudio } from './lib/audio-file.mjs';
import { TtsError } from './lib/tts-error.mjs';
import {
  PROVIDERS,
  PROVIDER_DOCS,
  resolveProviderName,
  resolveProviderConfig,
  synthesizeWav,
  listVoicesFor,
  formatVoiceTable,
  missingKeyGuidance,
} from './lib/provider.mjs';
import { loadApprovedTemplates } from './lib/approved-templates.mjs';
import { runPreflight } from './lib/preflight.mjs';
import {
  readState,
  writeState,
  buildManifest,
  writeManifest,
  outstandingEntries,
  writeJsonAtomic,
} from './lib/manifest.mjs';

const SMOKE_SET = ['en.digit.4', 'bn.digit.4', 'en.phrase.token-number', 'bn.phrase.token-number'];
const MAX_ATTEMPTS = 4;
const BACKOFF_BASE_MS = 1500;
const BACKOFF_CAP_MS = 30_000;

const USAGE = `
QUE-006 audio generation — Gemini TTS or ElevenLabs TTS

Usage:
  node scripts/que-006-audio/generate.mjs --all [options]
  node scripts/que-006-audio/generate.mjs --smoke [options]
  node scripts/que-006-audio/generate.mjs --en | --bn [options]
  node scripts/que-006-audio/generate.mjs --asset <id>[,<id>...] [options]
  node scripts/que-006-audio/generate.mjs --rebuild-manifest | --check-catalogue
  node scripts/que-006-audio/generate.mjs --list-voices

Selection:
  --all                 all ${CATALOGUE_ASSET_COUNT} catalogue assets
  --en                  the 14 English assets
  --bn                  the 14 Bangla assets
  --asset <ids>         explicit comma-separated asset ids
  --smoke               the 4-asset smoke set
  --limit <n>           stop after n selected assets (quota guard)

Provider:
  --provider <name>     ${PROVIDERS.join(' | ')} (default gemini; QUE006_TTS_PROVIDER also works)
  --model <id>          override the provider's model
  --voice-en <id>       override the English voice (Gemini name, or ElevenLabs voice id)
  --voice-bn <id>       override the Bangla voice
  --output-format <f>   ElevenLabs output_format (default wav_24000; wav_44100 needs Pro tier)
  --list-voices         print the voices this key can use, then exit

Behaviour:
  --force               regenerate even when a valid file already exists
  --dry-run             print the plan; no network calls, no writes
  --preflight-only      run key/model/voice/probe checks and stop
  --skip-preflight      skip the checks
  --no-probe            preflight without the small synthesis probe
  --rebuild-manifest    rebuild manifest.json from files on disk, no generation
  --check-catalogue     verify catalogue.mjs against the catalogue document and
                        the approved templates in content.js
  --help                this text

Environment:
  GEMINI_API_KEY        required for --provider gemini (also read from .env.local / .env)
  GEMINI_TTS_MODEL      default gemini-3.8-flash-tts
  GEMINI_VOICE_EN       default Kore
  GEMINI_VOICE_BN       default Kore
  GEMINI_TTS_STYLE_EN   optional speech_metadata style for English clips
  GEMINI_TTS_STYLE_BN   optional speech_metadata style for Bangla clips
  GEMINI_API_BASE       default https://generativelanguage.googleapis.com/v1beta

  ELEVEN_LABS_API_KEY   required for --provider elevenlabs (ELEVENLABS_API_KEY accepted too)
  ELEVENLABS_TTS_MODEL  default eleven_multilingual_v2 (eleven_flash_v2_5 is the cheaper option)
  ELEVENLABS_VOICE_ID_EN / ELEVENLABS_VOICE_ID_BN
                        required: no voice id is invented. Run --list-voices.
  ELEVENLABS_VOICE_ID   used for both languages when the per-language value is unset
  ELEVENLABS_OUTPUT_FORMAT  default wav_24000 (the body is a complete WAV, so no
                        decoder is needed; wav_44100 / pcm_44100 require Pro tier)
  ELEVENLABS_API_BASE   default https://api.elevenlabs.io/v1

Documents: ${PROVIDER_DOCS.gemini}
           ${PROVIDER_DOCS.elevenlabs}

Exit codes: 0 all selected assets valid | 1 asset failure(s) | 2 missing API key or bad
arguments | 3 stopped (auth/permission/quota/model/format) — resume later with the same command.
`;


/**
 * @param {string[]} argv
 */
export function parseArgs(argv) {
  const args = {
    selection: null, // 'all' | 'en' | 'bn' | 'smoke' | 'assets'
    assetIds: [],
    force: false,
    dryRun: false,
    preflightOnly: false,
    skipPreflight: false,
    probe: true,
    rebuildManifest: false,
    checkCatalogue: false,
    listVoices: false,
    limit: null,
    help: false,
    // Provider overrides: null means "take it from the environment".
    provider: null,
    model: null,
    voiceEn: null,
    voiceBn: null,
    outputFormat: null,
  };

  const setSelection = (value) => {
    if (args.selection && args.selection !== value) {
      const label = value === 'assets' ? '--asset' : `--${value}`;
      throw new Error(`conflicting selectors: --${args.selection} and ${label}`);
    }
    args.selection = value;
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    switch (arg) {
      case '--all': setSelection('all'); break;
      case '--en': setSelection('en'); break;
      case '--bn': setSelection('bn'); break;
      case '--smoke': setSelection('smoke'); break;
      case '--asset': {
        const value = argv[i + 1];
        if (!value || value.startsWith('--')) throw new Error('--asset needs a comma-separated list of asset ids');
        setSelection('assets');
        args.assetIds = value.split(',').map((id) => id.trim()).filter(Boolean);
        i += 1;
        break;
      }
      case '--limit': {
        const value = Number(argv[i + 1]);
        if (!Number.isInteger(value) || value < 1) throw new Error('--limit needs a positive integer');
        args.limit = value;
        i += 1;
        break;
      }
      case '--provider': {
        const value = (argv[i + 1] || '').trim().toLowerCase();
        if (!value || value.startsWith('--')) throw new Error(`--provider needs a name (${PROVIDERS.join(' | ')})`);
        if (!PROVIDERS.includes(value)) throw new Error(`unknown provider "${value}" (expected ${PROVIDERS.join(', ')})`);
        args.provider = value;
        i += 1;
        break;
      }
      case '--model': {
        const value = argv[i + 1];
        if (!value || value.startsWith('--')) throw new Error('--model needs a model id');
        args.model = value.trim();
        i += 1;
        break;
      }
      case '--voice-en': {
        const value = argv[i + 1];
        if (!value || value.startsWith('--')) throw new Error('--voice-en needs a voice name or id');
        args.voiceEn = value.trim();
        i += 1;
        break;
      }
      case '--voice-bn': {
        const value = argv[i + 1];
        if (!value || value.startsWith('--')) throw new Error('--voice-bn needs a voice name or id');
        args.voiceBn = value.trim();
        i += 1;
        break;
      }
      case '--voice': {
        const value = argv[i + 1];
        if (!value || value.startsWith('--')) throw new Error('--voice needs a voice name or id');
        args.voiceEn = value.trim();
        args.voiceBn = value.trim();
        i += 1;
        break;
      }
      case '--output-format': {
        const value = argv[i + 1];
        if (!value || value.startsWith('--')) throw new Error('--output-format needs a value such as wav_24000');
        args.outputFormat = value.trim();
        i += 1;
        break;
      }
      case '--list-voices': args.listVoices = true; break;
      case '--force': args.force = true; break;
      case '--dry-run': args.dryRun = true; break;
      case '--preflight-only': args.preflightOnly = true; break;
      case '--skip-preflight': args.skipPreflight = true; break;
      case '--no-probe': args.probe = false; break;
      case '--rebuild-manifest': args.rebuildManifest = true; break;
      case '--check-catalogue': args.checkCatalogue = true; break;
      case '--help': case '-h': args.help = true; break;
      default: throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}

/**
 * Resolve generation configuration for one provider.
 *
 * A thin wrapper over `provider.resolveProviderConfig` so every override is
 * resolved in one place, and `generate.mjs` itself stays provider-agnostic.
 *
 * @param {string} [provider] 'gemini' | 'elevenlabs'
 * @param {{model?: string|null, voiceEn?: string|null, voiceBn?: string|null,
 *   outputFormat?: string|null}} [overrides] values from the CLI
 */
export function resolveConfig(provider = 'gemini', overrides = {}) {
  return resolveProviderConfig(provider, overrides);
}

/** Turn the CLI selection into a concrete asset list. */
export function selectAssets(args) {
  let selected;
  switch (args.selection) {
    case 'en':
      selected = ASSETS.filter((asset) => asset.language === 'en');
      break;
    case 'bn':
      selected = ASSETS.filter((asset) => asset.language === 'bn');
      break;
    case 'smoke':
      selected = SMOKE_SET.map((id) => getAssetOrThrow(id));
      break;
    case 'assets': {
      const unknown = args.assetIds.filter((id) => !ASSET_BY_ID.has(id));
      if (unknown.length) {
        throw new Error(`unknown asset id(s): ${unknown.join(', ')}\nKnown ids:\n  ${ASSET_IDS.join('\n  ')}`);
      }
      selected = args.assetIds.map((id) => getAssetOrThrow(id));
      break;
    }
    case 'all':
    case null:
      selected = ASSETS.slice();
      break;
    default:
      throw new Error(`unhandled selection: ${args.selection}`);
  }

  if (args.limit) selected = selected.slice(0, args.limit);
  return selected;
}

function getAssetOrThrow(id) {
  const asset = ASSET_BY_ID.get(id);
  if (!asset) throw new Error(`unknown asset id: ${id}`);
  return asset;
}

/** Human-readable asset line prefix, e.g. `en phrase room-suffix` (from `en.phrase.room-suffix`). */
function label(asset) {
  const slug = asset.id.split('.').slice(2).join('.');
  return `${asset.language} ${asset.category} ${slug}`;
}

function sleep(ms) {
  return new Promise((resolve) => { setTimeout(resolve, ms); });
}

function backoffMs(attempt) {
  const base = Math.min(BACKOFF_BASE_MS * 2 ** (attempt - 1), BACKOFF_CAP_MS);
  return Math.round(base * (0.75 + Math.random() * 0.5));
}

/** Record one asset as generated in the state file (single source of truth for what ran). */
function recordState(state, asset, entry) {
  state.assets[asset.id] = {
    ...entry,
    spokenText: asset.spokenText,
    filename: asset.filename,
    recordedAt: new Date().toISOString(),
  };
}

/**
 * Write the punctuation-only asset as a silent WAV of the documented pause
 * length — no API call, because there is nothing to say.
 */
function generateSynthetic(asset) {
  const delivery = audioPathFor(asset);
  const master = masterPathFor(asset);
  const options = { durationMs: PUNCTUATION_PAUSE_MS };
  const info = writeSilentWav(delivery, options);
  fs.mkdirSync(path.dirname(master), { recursive: true });
  fs.copyFileSync(delivery, master);
  const record = inspectAudioFile(delivery, { expectSilence: true });
  if (!record.decodable || !record.silent) {
    return {
      ok: false,
      detail: `synthetic pause failed validation: ${record.problems.join('; ') || 'unexpected signal'}`,
      record,
    };
  }
  return { ok: true, detail: `${PUNCTUATION_PAUSE_MS} ms silent WAV`, record, info };
}

/**
 * Generate one spoken asset, with bounded retries.
 *
 * Retry policy comes from `classifyHttpError`: transport hiccups, 429 and 5xx are
 * retried with exponential backoff; 400/401/403/404 stop the whole run because
 * they cannot fix themselves inside a loop.
 */
async function generateSpokenAsset(ctx, asset) {
  const { config, apiKey } = ctx;
  const voice = config.voices[asset.language];
  // The catalogue's leading/trailing spaces exist so the clips concatenate with
  // breathing room in the sentence. They are composition padding, not dictation,
  // so the request text is trimmed while the catalogue text is recorded verbatim.
  const requestText = recordedTextFor(asset).trim();
  const style = config.styles[asset.language];

  let attempts = 0;
  let lastError = null;

  while (attempts < MAX_ATTEMPTS) {
    attempts += 1;
    try {
      const audio = await synthesizeWav(config, {
        apiKey,
        voice,
        text: requestText,
        style,
      });

      const delivery = audioPathFor(asset);
      const master = masterPathFor(asset);
      fs.mkdirSync(path.dirname(delivery), { recursive: true });
      fs.mkdirSync(path.dirname(master), { recursive: true });
      fs.writeFileSync(master, audio.buffer);

      const detected = detectContainer(audio.buffer);
      if (detected !== 'wav') {
        return {
          ok: false,
          stopRun: false,
          attempts,
          detail: `the provider adapter returned a ${detected === 'unknown' ? 'unrecognised' : detected.toUpperCase()} `
            + `container (${audio.mimeType}) instead of WAV; only WAV is written, so nothing was delivered`,
          failureKind: 'unexpected-format',
        };
      }

      fs.writeFileSync(delivery, audio.buffer);
      const record = inspectAudioFile(delivery);
      if (!record.decodable || !record.durationMs || record.silent) {
        // Do not leave an unusable file where the application would serve it.
        try { fs.rmSync(delivery, { force: true }); } catch { /* best effort */ }
        return {
          ok: false,
          stopRun: false,
          attempts,
          detail: `written file failed validation: ${record.problems.join('; ') || 'no duration or silent'}`,
          failureKind: 'invalid-audio',
          record,
        };
      }

      return {
        ok: true,
        attempts,
        record,
        delivery,
        master,
        meta: {
          provider: audio.meta.provider,
          model: config.model,
          voice,
          style: style || null,
          requestText,
          responsePath: audio.responsePath,
          mimeType: audio.mimeType,
          requestedFormat: audio.meta.requestedFormat,
          deliveredFormat: audio.meta.deliveredFormat,
          transcode: audio.meta.transcode,
          sha256: record.sha256,
          bytes: record.size,
          durationMs: record.durationMs,
        },
      };
    } catch (err) {
      lastError = err;
      const isTts = err instanceof TtsError;
      const stopRun = isTts ? Boolean(err.stopRun) : false;
      const retryable = isTts ? Boolean(err.retryable) : true;
      const detail = redact(isTts ? `${err.kind}: ${err.message}` : String(err?.message || err), apiKey);

      if (stopRun || !retryable || attempts >= MAX_ATTEMPTS) {
        return {
          ok: false,
          stopRun,
          attempts,
          detail,
          failureKind: isTts ? err.kind : 'error',
          guidance: isTts ? err.guidance || null : null,
        };
      }
      const wait = backoffMs(attempts);
      console.log(`      retry ${attempts}/${MAX_ATTEMPTS} in ${(wait / 1000).toFixed(1)}s — ${detail}`);
      await sleep(wait);
    }
  }

  return {
    ok: false,
    stopRun: false,
    attempts,
    detail: lastError ? String(lastError.message || lastError) : 'unknown failure',
    failureKind: 'exhausted',
  };
}

/** Container name from the raw buffer, without parsing it. */
function detectContainer(buffer) {
  if (!buffer || buffer.length < 12) return 'unknown';
  if (buffer.toString('ascii', 0, 4) === 'RIFF' && buffer.toString('ascii', 8, 12) === 'WAVE') return 'wav';
  if (buffer[0] === 0x49 && buffer[1] === 0x44 && buffer[2] === 0x33) return 'mp3';
  if (buffer[0] === 0xff && (buffer[1] & 0xe0) === 0xe0) return 'mp3';
  return 'unknown';
}

/**
 * Read the approved announcement templates from the frontend source.
 *
 * Delegates to `lib/approved-templates.mjs`; re-exported here so the CLI keeps a
 * single import surface.
 */
export { loadApprovedTemplates };

/**
 * `--check-catalogue`: prove three things before any audio is made —
 * the code table matches the catalogue document, the composed templates match
 * the approved wording, and the count is 14 + 14.
 */
export function checkCatalogue() {
  const doc = diffAgainstDoc(REPO_ROOT);
  const approved = loadApprovedTemplates();
  const composed = diffComposedAgainstApproved(approved);
  const byLanguage = { en: ASSETS.filter((a) => a.language === 'en').length, bn: ASSETS.filter((a) => a.language === 'bn').length };

  console.log('Catalogue checks');
  console.log(`  asset table          ${ASSET_IDS.length} entries (en ${byLanguage.en}, bn ${byLanguage.bn})`);
  console.log(`  vs ${'docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md'}`);
  if (doc.ok) {
    console.log(`    OK — ${doc.documentRows} document rows agree with catalogue.mjs`);
  } else {
    console.log(`    MISMATCH — ${doc.mismatches.length} finding(s)`);
    for (const item of doc.mismatches) console.log(`      - ${item}`);
  }
  console.log('  composed templates vs approved wording (content.js)');
  if (composed.length === 0) {
    console.log('    OK — with-room and no-room templates compose identically for en and bn');
  } else {
    for (const finding of composed) {
      console.log(`    MISMATCH ${finding.language}.${finding.variant}`);
      console.log(`      catalogue: ${JSON.stringify(finding.catalogue)}`);
      console.log(`      approved : ${JSON.stringify(finding.approved)}`);
    }
  }
  const ok = doc.ok && composed.length === 0
    && ASSET_IDS.length === CATALOGUE_ASSET_COUNT
    && byLanguage.en === 14 && byLanguage.bn === 14;

  const overrideIds = Object.keys(SPOKEN_TEXT_OVERRIDES);
  console.log('  declared spoken-text overrides (recorded text differs from the catalogue cell)');
  if (overrideIds.length === 0) {
    console.log('    none');
  } else {
    for (const id of overrideIds) {
      console.log(`    ${id}`);
      console.log(`      recorded: ${JSON.stringify(SPOKEN_TEXT_OVERRIDES[id].spokenText)}`);
      console.log(`      reason  : ${SPOKEN_TEXT_OVERRIDES[id].reason}`);
    }
    console.log('    These are open items for the product owner: the catalogue document still holds the old text.');
  }

  console.log(`  result               ${ok ? 'PASS' : 'FAIL'}`);
  return ok;
}

/** Print the plan without touching the network or the disk. */
function printPlan(selected, config, { hasKey, keySource }) {
  const state = readState(STATE_PATH);
  console.log('Dry run — nothing will be generated or written.\n');
  console.log(`  provider         ${config.provider} (${config.label})`);
  console.log(`  model            ${config.model}`);
  console.log(`  voices           en=${config.voices.en ?? '(not configured)'}  bn=${config.voices.bn ?? '(not configured)'}`);
  console.log(`  styles           en=${config.styles.en ?? '(none)'}  bn=${config.styles.bn ?? '(none)'}`);
  if (config.outputFormat) console.log(`  output format    ${config.outputFormat}`);
  console.log(`  api base         ${config.apiBase}`);
  console.log(`  api key          ${hasKey ? `present (${keySource})` : 'MISSING — generation would stop with exit 2'}`);
  console.log('  delivery root    frontend/public/audio');
  console.log('  master root      scripts/que-006-audio/.work/master');
  console.log(`\n  ${selected.length} asset(s) selected:`);
  for (const asset of selected) {
    const synthetic = asset.synthetic === 'silence';
    const existing = inspectAudioFile(audioPathFor(asset), { expectSilence: synthetic });
    const known = state.assets?.[asset.id];
    const status = !existing.exists
      ? 'absent'
      : existing.decodable && !existing.problems.length
        ? (known?.sha256 && existing.sha256 === known.sha256 ? 'valid, would skip' : 'valid, unrecorded')
        : 'invalid, would regenerate';
    const mode = synthetic ? 'synthetic pause' : `TTS ${config.voices[asset.language] ?? '(no voice)'}`;
    console.log(`    ${asset.id.padEnd(26)} ${mode.padEnd(24)} ${status}`);
  }
}

/**
 * Generate the selected assets, updating state and the manifest as it goes.
 *
 * @returns {Promise<{exitCode: number, results: any[], stopped: boolean, stopReason: string|null}>}
 */
async function runGeneration(ctx, selected) {
  const { config, apiKey, state } = ctx;
  const results = [];
  let stopped = false;
  let stopReason = null;

  for (let index = 0; index < selected.length; index += 1) {
    const asset = selected[index];
    const position = `[${index + 1}/${selected.length}]`;
    const synthetic = asset.synthetic === 'silence';
    const delivery = audioPathFor(asset);

    // Resume: a file that already validates is not regenerated (and not re-billed).
    if (!ctx.args.force) {
      const existing = inspectAudioFile(delivery, { expectSilence: synthetic });
      if (existing.exists && existing.decodable && existing.durationMs && !existing.problems.length) {
        const known = state.assets?.[asset.id];
        const checksumAgrees = !known?.sha256 || known.sha256 === existing.sha256;
        if (checksumAgrees) {
          console.log(`${position} ${label(asset)} — skip (valid ${describeAudio(existing)}, ${existing.durationMs} ms)`);
          results.push({ id: asset.id, status: 'skipped', detail: 'existing file is valid', sha256: existing.sha256, durationMs: existing.durationMs });
          continue;
        }
        console.log(`${position} ${label(asset)} — file differs from the recorded checksum; regenerating`);
      }
    }

    if (synthetic) {
      const outcome = generateSynthetic(asset);
      if (!outcome.ok) {
        console.log(`${position} ${label(asset)} — FAILED: ${outcome.detail}`);
        results.push({ id: asset.id, status: 'failed', detail: outcome.detail, failureKind: 'synthetic' });
        continue;
      }
      recordState(state, asset, {
        generationStatus: 'generated',
        source: 'synthetic-silence',
        model: null,
        voice: null,
        style: null,
        responsePath: null,
        generatedAt: new Date().toISOString(),
        attempts: 0,
        sha256: outcome.record.sha256,
        bytes: outcome.record.size,
        durationMs: outcome.record.durationMs,
        note: `Punctuation-only asset written as a ${PUNCTUATION_PAUSE_MS} ms silent pause; the playback engine must pause here, not speak.`,
      });
      writeState(STATE_PATH, state);
      console.log(`${position} ${label(asset)} — ok (synthetic ${PUNCTUATION_PAUSE_MS} ms pause, ${outcome.record.size} B)`);
      results.push({ id: asset.id, status: 'generated', source: 'synthetic-silence', sha256: outcome.record.sha256, durationMs: outcome.record.durationMs, detail: outcome.detail });
      continue;
    }

    console.log(`${position} ${label(asset)} — "${recordedTextFor(asset).trim()}" [${config.voices[asset.language]}]`);
    const outcome = await generateSpokenAsset(ctx, asset);

    if (outcome.ok) {
      recordState(state, asset, {
        generationStatus: 'generated',
        source: `${outcome.meta.provider}-tts`,
        provider: outcome.meta.provider,
        model: outcome.meta.model,
        voice: outcome.meta.voice,
        style: outcome.meta.style,
        responsePath: outcome.meta.responsePath,
        requestedFormat: outcome.meta.requestedFormat,
        deliveredFormat: outcome.meta.deliveredFormat,
        transcode: outcome.meta.transcode,
        generatedAt: new Date().toISOString(),
        attempts: outcome.attempts,
        sha256: outcome.meta.sha256,
        bytes: outcome.meta.bytes,
        durationMs: outcome.meta.durationMs,
        requestText: outcome.meta.requestText,
        mimeType: outcome.meta.mimeType,
      });
      writeState(STATE_PATH, state);
      console.log(`      ok — ${describeAudio(outcome.record)}, ${outcome.record.durationMs} ms, ${(outcome.record.size / 1024).toFixed(1)} KB, sha256 ${outcome.record.sha256.slice(0, 12)}…`);
      results.push({
        id: asset.id, status: 'generated', sha256: outcome.record.sha256,
        durationMs: outcome.record.durationMs, bytes: outcome.record.size,
        attempts: outcome.attempts, model: outcome.meta.model, voice: outcome.meta.voice,
      });
      continue;
    }

    console.log(`      FAILED (${outcome.failureKind}, attempt ${outcome.attempts}): ${outcome.detail}`);
    if (outcome.guidance) console.log(`      guidance: ${outcome.guidance}`);
    results.push({
      id: asset.id, status: 'failed', detail: outcome.detail,
      failureKind: outcome.failureKind, attempts: outcome.attempts, guidance: outcome.guidance || null,
    });

    if (outcome.stopRun) {
      stopped = true;
      stopReason = `${outcome.failureKind}: ${outcome.detail}`;
      console.log(`\nRun stopped after ${index + 1}/${selected.length}: this failure cannot fix itself by retrying.`);
      console.log('Fix the cause, then re-run the same command — valid files are skipped and nothing is re-billed.');
      break;
    }
  }

  const failed = results.some((entry) => entry.status === 'failed');
  return { exitCode: stopped ? 3 : failed ? 1 : 0, results, stopped, stopReason };
}

/**
 * Print the closing summary: what ran, what is on disk, what a human still owes.
 */
function printSummary({ results, manifest, startedAt, preflight }) {
  const counts = results.reduce((acc, entry) => {
    acc[entry.status] = (acc[entry.status] || 0) + 1;
    return acc;
  }, /** @type {Record<string, number>} */ ({}));
  const seconds = ((Date.now() - startedAt) / 1000).toFixed(1);

  console.log('\nRun summary');
  console.log(`  generated ${counts.generated || 0} · skipped ${counts.skipped || 0} · failed ${counts.failed || 0}  (${seconds}s)`);
  if (preflight) {
    const passed = preflight.checks.filter((check) => check.status === 'pass').length;
    console.log(`  preflight ${preflight.ok ? 'passed' : 'FAILED'} (${passed}/${preflight.checks.length} checks)`);
    for (const warning of preflight.warnings) console.log(`    warning: ${warning}`);
  }
  console.log(`  catalogue ${manifest.summary.ready}/${manifest.summary.total} assets ready`
    + ` (en ${manifest.catalogue.byLanguage.en}, bn ${manifest.catalogue.byLanguage.bn})`);
  if (manifest.summary.missing) console.log(`    missing: ${manifest.summary.missing}`);
  if (manifest.summary.invalid) console.log(`    invalid: ${manifest.summary.invalid}`);
  if (manifest.summary.modifiedSinceGeneration) console.log(`    modified since generation: ${manifest.summary.modifiedSinceGeneration}`);
  if (manifest.summary.unrecorded) console.log(`    present but unrecorded in state: ${manifest.summary.unrecorded}`);

  const failed = results.filter((entry) => entry.status === 'failed');
  if (failed.length) {
    console.log('  failures:');
    for (const entry of failed) console.log(`    ${entry.id}: ${entry.detail}`);
  }

  console.log('\nStill outstanding before these clips can be used in the demo:');
  console.log('  1. Human listening review of every clip — Bangla pronunciation and intonation in');
  console.log('     particular — by a native or fluent speaker. Nothing here confirms that.');
  console.log('  2. A prerecorded-audio playback engine in the frontend. The app still speaks via');
  console.log('     the browser speechSynthesis path; manifest.json is not consumed yet.');
  console.log('  3. A loudness/level check on the target clinic hardware; this utility applies');
  console.log('     no loudness normalisation.');
}

/** `--rebuild-manifest`: derive manifest.json from the files on disk. */
export function rebuildManifest(config, { quiet = false } = {}) {
  const state = readState(STATE_PATH);
  const manifest = buildManifest({
    state,
    generator: {
      utility: 'scripts/que-006-audio/generate.mjs',
      catalogueTable: 'scripts/que-006-audio/catalogue.mjs',
      provider: config.provider,
      providerLabel: config.label,
      model: config.model,
      voices: config.voices,
      styles: config.styles,
      apiBase: config.apiBase,
      outputFormat: config.outputFormat,
      note: 'Provider, model and voice are recorded per asset as actually used; the values above are the current configuration, not a claim about older files.',
    },
  });
  writeManifest(MANIFEST_PATH, manifest);
  if (!quiet) {
    const outstanding = outstandingEntries(manifest);
    console.log(`Manifest written: frontend/public/audio/manifest.json`);
    console.log(`  ${manifest.summary.ready}/${manifest.summary.total} assets ready; ${outstanding.length} outstanding`);
    for (const entry of outstanding) {
      console.log(`    ${entry.validationStatus.padEnd(26)} ${entry.id}  ${entry.filename}${entry.problems.length ? ` — ${entry.problems.join('; ')}` : ''}`);
    }
  }
  return manifest;
}

/**
 * `--list-voices`: print the voices this key can use, then exit.
 *
 * No default voice id is invented anywhere in this utility. A guessed id either
 * 404s or — worse — resolves to a different voice than the one intended, so the
 * ids printed here are the only ones a human should enter into
 * `ELEVENLABS_VOICE_ID_EN` / `_BN` (or `GEMINI_VOICE_EN` / `_BN`).
 */
async function listVoicesCommand(config, apiKey, keyResolution) {
  if (!apiKey) {
    console.log(`No key resolved for ${config.label} (looked in: ${keyResolution.source}).`);
    console.log(`Set ${config.keyVars[0]} and re-run --list-voices.`);
    return 2;
  }
  try {
    const voices = await listVoicesFor(config, apiKey);
    console.log(`Voices available to this key — ${config.label} (${config.apiBase})`);
    console.log(`  ${voices.length} voice(s)`);
    for (const line of formatVoiceTable(voices)) console.log(line);
    console.log('\nChoose ids and set ELEVENLABS_VOICE_ID_EN / ELEVENLABS_VOICE_ID_BN (or GEMINI_VOICE_EN / _BN).');
    console.log('Nothing was generated and no file was written.');
    return 0;
  } catch (err) {
    const message = err instanceof TtsError ? `${err.kind}: ${err.message}` : String(err?.message || err);
    console.error(`ERROR could not list voices: ${redact(message, apiKey)}`);
    if (err?.guidance) console.error(`  ${err.guidance}`);
    if (err?.kind === 'key-permissions') {
      // A key that may synthesize but may not list is still usable: the ids can be
      // read off the dashboard instead. Saying so prevents a dead end.
      console.error('  If you would rather not add the read scope, copy a voice id from the ElevenLabs dashboard');
      console.error('  (Voices -> pick a voice -> ID) and pass it as --voice-en/--voice-bn, or set');
      console.error('  ELEVENLABS_VOICE_ID_EN / ELEVENLABS_VOICE_ID_BN in .env.local. An id is only valid if that');
      console.error('  account owns the voice.');
    }
    return 3;
  }
}

async function main(argv) {
  const startedAt = Date.now();
  const startedAtIso = new Date(startedAt).toISOString();

  let args;
  try {
    args = parseArgs(argv);
  } catch (err) {
    console.error(`ERROR ${err.message}`);
    console.error(USAGE);
    return 2;
  }

  if (args.help) {
    console.log(USAGE);
    return 0;
  }

  let provider;
  try {
    provider = resolveProviderName(args.provider);
  } catch (err) {
    console.error(`ERROR ${err.message}`);
    return 2;
  }

  const config = resolveConfig(provider, {
    model: args.model,
    voiceEn: args.voiceEn,
    voiceBn: args.voiceBn,
    outputFormat: args.outputFormat,
  });

  if (args.checkCatalogue) return checkCatalogue() ? 0 : 1;
  if (args.rebuildManifest) {
    rebuildManifest(config);
    return 0;
  }

  let selected;
  try {
    selected = selectAssets(args);
  } catch (err) {
    console.error(`ERROR ${err.message}`);
    return 2;
  }
  if (selected.length === 0) {
    console.error('ERROR nothing selected');
    return 2;
  }

  const needsApi = selected.some((asset) => asset.synthetic !== 'silence');
  const keyResolution = resolveApiKey(provider);
  const apiKey = keyResolution.key;
  const keySource = keyResolution.source;

  // A value that cannot be a real key must never shadow one that can, and the
  // substitution is always announced. Cause seen in practice: a stale
  // `ELEVEN_LABS_API_KEY=sk_xxx` in one shell hiding a complete key in `.env.local`.
  for (const skippedEntry of keyResolution.ignored || []) {
    console.warn(
      `WARNING ignored an unusable key value from ${skippedEntry.source} `
      + `(${skippedEntry.length} characters, which cannot be a ${provider} key); `
      + `the value from ${keySource} is used instead. Remove the stale value if it was not intended.`,
    );
  }

  if (args.listVoices) return listVoicesCommand(config, apiKey, keyResolution);

  if (args.dryRun) {
    printPlan(selected, config, { hasKey: Boolean(apiKey), keySource });
    return 0;
  }

  if (needsApi && !apiKey) {
    const needingApi = selected.filter((asset) => asset.synthetic !== 'silence').length;
    for (const line of missingKeyGuidance(config, keyResolution, [
      `  Selected: ${selected.length} asset(s), ${needingApi} needing the API.`,
    ])) console.error(line);
    return 2;
  }

  console.log(`QUE-006 TTS generation — ${config.label}`);
  console.log(`  selection ${args.selection || 'all'} — ${selected.length} asset(s), ${selected.filter((a) => a.synthetic !== 'silence').length} via API`);
  console.log(`  model ${config.model}${config.outputFormat ? ` · output ${config.outputFormat}` : ''}`
    + ` · voices en=${config.voices.en ?? 'none'} bn=${config.voices.bn ?? 'none'} · key from ${keySource}`);

  const overridden = selected.filter((asset) => SPOKEN_TEXT_OVERRIDES[asset.id]);
  if (overridden.length) {
    console.log('\n  Declared spoken-text override(s) in this selection:');
    for (const asset of overridden) {
      console.log(`    ${asset.id}: catalogue ${JSON.stringify(asset.spokenText)} → recorded ${JSON.stringify(SPOKEN_TEXT_OVERRIDES[asset.id].spokenText)}`);
    }
    console.log('    Reason recorded in catalogue.mjs SPOKEN_TEXT_OVERRIDES; open item for the product owner.');
  }

  return runWithPreflight({ argv, args, config, apiKey, keySource, selected, needsApi, startedAt, startedAtIso });
}

/** Preflight, generate, then rebuild the manifest and persist the run record. */
async function runWithPreflight({ argv, args, config, apiKey, keySource, selected, needsApi, startedAt, startedAtIso }) {
  let preflight = null;

  if (needsApi && !args.skipPreflight) {
    // Probe only the languages this selection actually needs, so an English-only
    // run is not blocked by a Bangla voice that is not configured yet — and a
    // Bangla probe is never skipped just because English passed.
    const voiceTargets = Array.from(new Set(
      selected.filter((asset) => asset.synthetic !== 'silence').map((asset) => asset.language),
    )).map((language) => ({ language, voice: config.voices[language] ?? null }));

    console.log('\nPreflight');
    preflight = await runPreflight({
      provider: config.provider,
      apiBase: config.apiBase,
      apiKey,
      model: config.model,
      voices: voiceTargets.map((target) => target.voice).filter(Boolean),
      voiceTargets,
      outputFormat: config.outputFormat,
      probe: args.probe,
    });
    for (const check of preflight.checks) {
      console.log(`  [${check.status.padEnd(7)}] ${check.name}: ${redact(check.detail, apiKey)}`);
    }
    for (const warning of preflight.warnings) console.log(`  warning: ${warning}`);

    if (!preflight.ok) {
      console.error('\nPreflight failed — generation did not start.');
      for (const failure of preflight.failures) console.error(`  ${redact(failure, apiKey)}`);
      writeJsonAtomic(LAST_RUN_PATH, {
        startedAt: startedAtIso,
        finishedAt: new Date().toISOString(),
        command: `generate.mjs ${argv.join(' ')}`,
        outcome: 'blocked-preflight',
        config: { provider: config.provider, model: config.model, voices: config.voices, apiBase: config.apiBase, outputFormat: config.outputFormat },
        selection: selected.map((asset) => asset.id),
        results: [],
        preflight: {
          ok: false,
          checks: preflight.checks,
          failures: preflight.failures.map((entry) => redact(entry, apiKey)),
          warnings: preflight.warnings,
        },
      });
      console.error('Checks recorded in scripts/que-006-audio/.work/last-run.json');
      return 3;
    }
    console.log('  preflight passed\n');
  } else if (needsApi) {
    console.log('\nPreflight skipped by --skip-preflight: model and voice availability are unproven for this run.\n');
  }

  const ctx = { config, apiKey, keySource, args, state: readState(STATE_PATH), startedAt };
  const run = await runGeneration(ctx, selected);

  const manifest = rebuildManifest(config, { quiet: true });
  writeJsonAtomic(LAST_RUN_PATH, {
    startedAt: startedAtIso,
    finishedAt: new Date().toISOString(),
    command: `generate.mjs ${argv.join(' ')}`,
    outcome: run.stopped ? 'stopped' : run.exitCode === 0 ? 'completed' : 'completed-with-failures',
    stopReason: run.stopReason,
    config: { provider: config.provider, model: config.model, voices: config.voices, styles: config.styles, apiBase: config.apiBase, outputFormat: config.outputFormat },
    selection: selected.map((asset) => asset.id),
    results: run.results,
    preflight: preflight ? { ok: preflight.ok, checks: preflight.checks, warnings: preflight.warnings } : null,
    manifestSummary: manifest.summary,
  });

  printSummary({ results: run.results, manifest, startedAt, preflight });
  console.log('\nWritten: frontend/public/audio/**/*.wav and frontend/public/audio/manifest.json,');
  console.log('         scripts/que-006-audio/.work/state.json and .work/last-run.json');
  return run.exitCode;
}

const invokedDirectly = (() => {
  const entry = process.argv[1];
  if (!entry) return false;
  try {
    return path.resolve(entry) === fileURLToPath(import.meta.url);
  } catch {
    return false;
  }
})();

if (invokedDirectly) {
  main(process.argv.slice(2))
    .then((code) => { process.exitCode = code; })
    .catch((err) => {
      console.error(`UNEXPECTED ${err && err.stack ? err.stack : err}`);
      process.exitCode = 1;
    });
}
