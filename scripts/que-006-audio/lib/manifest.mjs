/**
 * Manifest and generation-state handling for the QUE-006 audio utility.
 *
 * Two files, two purposes, deliberately separated:
 *
 *   - `scripts/que-006-audio/.work/state.json` — what this utility knows it did
 *     (model, voice, timestamp, attempts, checksum at write time). Never served.
 *   - `frontend/public/audio/manifest.json` — what the application may consume,
 *     derived from the catalogue **and** from what is actually on disk now.
 *
 * The manifest never claims more than the files prove: an entry is `ready` only
 * when the file exists, parses, has a positive duration, and its checksum either
 * matches the recorded generation or was never recorded (flagged `unrecorded`).
 * A file whose checksum no longer matches what was generated is reported as
 * `modified-since-generation` rather than silently blessed.
 */

import fs from 'node:fs';
import path from 'node:path';

import {
  ASSETS,
  CATALOGUE_DOC,
  CATALOGUE_VERSION,
  CATALOGUE_ASSET_COUNT,
  COUNT_BY_LANGUAGE,
  PUNCTUATION_ASSET_ID,
  PUNCTUATION_PAUSE_MS,
} from '../catalogue.mjs';
import { audioPathFor, masterPathFor } from './paths.mjs';
import { inspectAudioFile, describeAudio } from './audio-file.mjs';

const MANIFEST_VERSION = '1.0';

/** Read the generation-state file, tolerating absence and corruption. */
export function readState(statePath) {
  try {
    const parsed = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    if (parsed && typeof parsed === 'object' && parsed.assets && typeof parsed.assets === 'object') return parsed;
  } catch {
    // A missing or unreadable state file is normal on first run: it means the
    // utility has no record of generating anything yet.
  }
  return { version: 1, assets: {} };
}

/** Write JSON atomically: temp file in the same directory, then rename. */
export function writeJsonAtomic(filePath, value) {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
  const temp = path.join(dir, `.${path.basename(filePath)}.${process.pid}.tmp`);
  fs.writeFileSync(temp, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  fs.renameSync(temp, filePath);
}

export function writeState(statePath, state) {
  writeJsonAtomic(statePath, state);
}

/**
 * Validate one asset on disk and merge it with what the state file recorded.
 *
 * @param {object} asset catalogue row
 * @param {{assets: Record<string, any>}} state
 */
export function describeAssetFromDisk(asset, state) {
  const expectSilence = asset.synthetic === 'silence';
  const filePath = audioPathFor(asset);
  const record = inspectAudioFile(filePath, { expectSilence });
  const recorded = state.assets?.[asset.id] || null;

  let validationStatus;
  if (!record.exists) validationStatus = 'missing';
  else if (record.size === 0) validationStatus = 'empty';
  else if (!record.decodable) validationStatus = 'invalid';
  else if (record.silent && !expectSilence) validationStatus = 'silent';
  else if (!record.durationMs) validationStatus = 'zero-duration';
  else if (recorded?.sha256 && record.sha256 && recorded.sha256 !== record.sha256) validationStatus = 'modified-since-generation';
  else if (!recorded) validationStatus = 'unrecorded';
  else validationStatus = 'ready';

  return {
    id: asset.id,
    language: asset.language,
    category: asset.category,
    spokenText: asset.spokenText,
    filename: asset.filename,
    required: asset.required,
    usage: asset.usage,
    audioFormat: describeAudio(record),
    mimeType: record.mimeType,
    sampleRate: record.sampleRate,
    channels: record.channels,
    bitsPerSample: record.bitsPerSample,
    durationMs: record.durationMs,
    durationSeconds: record.durationSeconds === null ? null : Number(record.durationSeconds.toFixed(3)),
    fileSizeBytes: record.size,
    sha256: record.sha256,
    peakAmplitude: record.peakAmplitude,
    decodable: record.decodable,
    decodeVerifiedBy: record.decodeVerifiedBy,
    validationStatus,
    problems: record.problems,
    generation: recorded
      ? {
          status: recorded.generationStatus || 'generated',
          source: recorded.source || null,
          provider: recorded.provider || null,
          model: recorded.model || null,
          voice: recorded.voice || null,
          style: recorded.style ?? null,
          responsePath: recorded.responsePath || null,
          requestedFormat: recorded.requestedFormat || null,
          deliveredFormat: recorded.deliveredFormat || null,
          transcode: recorded.transcode || null,
          generatedAt: recorded.generatedAt || null,
          attempts: recorded.attempts ?? null,
          masterFile: fs.existsSync(masterPathFor(asset)) ? `scripts/que-006-audio/.work/master/${asset.filename}` : null,
        }
      : {
          status: 'not-recorded',
          source: null,
          provider: null,
          model: null,
          voice: null,
          style: null,
          responsePath: null,
          generatedAt: null,
          attempts: null,
          masterFile: fs.existsSync(masterPathFor(asset)) ? `scripts/que-006-audio/.work/master/${asset.filename}` : null,
        },
    playbackNote: expectSilence
      ? `Punctuation-only asset: the engine must insert a ${PUNCTUATION_PAUSE_MS} ms pause here instead of playing speech. The file is a deliberately silent ${PUNCTUATION_PAUSE_MS} ms WAV.`
      : null,
    humanReview: {
      required: true,
      reason: asset.language === 'bn'
        ? 'Bangla pronunciation and intonation must be confirmed by a native speaker before demo use.'
        : 'English pronunciation, pace and loudness must be confirmed by listening before demo use.',
    },
  };
}
/**
 * Build the manifest for the whole catalogue.
 *
 * @param {{state: {assets: Record<string, any>}, generator: object}} options
 */
export function buildManifest(options) {
  const assets = ASSETS.map((asset) => describeAssetFromDisk(asset, options.state));
  const counts = assets.reduce((acc, entry) => {
    acc[entry.validationStatus] = (acc[entry.validationStatus] || 0) + 1;
    return acc;
  }, /** @type {Record<string, number>} */ ({}));

  const readyCount = counts.ready || 0;
  const allReady = readyCount === CATALOGUE_ASSET_COUNT;

  return {
    version: MANIFEST_VERSION,
    generatedAt: new Date().toISOString(),
    catalogue: {
      document: CATALOGUE_DOC,
      version: CATALOGUE_VERSION,
      assetCount: CATALOGUE_ASSET_COUNT,
      byLanguage: COUNT_BY_LANGUAGE,
      languages: ['en', 'bn'],
    },
    generator: options.generator,
    summary: {
      total: assets.length,
      ready: readyCount,
      missing: counts.missing || 0,
      invalid: (counts.invalid || 0) + (counts.empty || 0) + (counts['zero-duration'] || 0) + (counts.silent || 0),
      modifiedSinceGeneration: counts['modified-since-generation'] || 0,
      unrecorded: counts.unrecorded || 0,
      catalogueComplete: allReady,
    },
    playable: {
      // The application-side prerecorded-audio engine does not exist yet; the
      // manifest says so rather than implying these files are already used.
      readyForPlaybackEngine: allReady,
      integratedWithApplication: false,
      note: 'Files and manifest are complete for the catalogue above. The AMSDP frontend still uses browser speechSynthesis; a prerecorded-audio engine must load this manifest before these clips can be heard in the demo.',
      humanReviewOutstanding: true,
    },
    assets,
  };
}

/** Write the manifest atomically to the public audio directory. */
export function writeManifest(manifestPath, manifest) {
  writeJsonAtomic(manifestPath, manifest);
}

/**
 * Report manifest entries that are not `ready`, so callers can print a short
 * actionable list instead of the whole document.
 *
 * @param {ReturnType<typeof buildManifest>} manifest
 */
export function outstandingEntries(manifest) {
  return manifest.assets.filter((entry) => entry.validationStatus !== 'ready');
}

