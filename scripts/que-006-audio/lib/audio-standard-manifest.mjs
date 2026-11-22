/**
 * QUE-006 — build `frontend/public/audio/manifest.json` from the bytes on disk.
 *
 * The manifest is a description of what exists, never an aspiration. Every
 * checksum is computed here from the file it names, and every status comes from
 * `evaluateAsset()`, the same function the validator uses.
 *
 * Human approval is the one field that cannot be derived. `humanReviewStatus`
 * defaults to `pending` and is only carried forward from a previous manifest when
 * a human set it on *exactly the same playback bytes* (checksum match). Converting
 * a clip therefore resets its approval, which is the correct behaviour: a
 * re-encoded file has not been listened to by anyone.
 */

import fs from 'node:fs';
import path from 'node:path';

import {
  ASSET_SPECS,
  INTENTIONAL_PAUSE_MS,
  MANIFEST_SCHEMA,
  MASTER_FORMAT,
  PLAYBACK_FORMAT,
  STANDARDISATION_RECORD_PATH,
  describeMasterFormat,
  describePlaybackFormat,
  evaluateAsset,
} from './audio-standard.mjs';
import { readBackupRecord } from './audio-backup.mjs';
import { MANIFEST_PATH } from './paths.mjs';
import { detectDecoder } from './decode.mjs';
import { CATALOGUE_ASSET_COUNT, CATALOGUE_DOC, CATALOGUE_VERSION } from '../catalogue.mjs';

/** Human-review values a person may set; anything else is treated as pending. */
const HUMAN_VALUES = new Set(['pending', 'approved', 'rejected']);

/** Read the previous manifest, tolerating absence or corruption. */
export function readPreviousManifest(manifestPath = MANIFEST_PATH) {
  try {
    const parsed = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    if (parsed && typeof parsed === 'object' && Array.isArray(parsed.assets)) return parsed;
  } catch {
    // First run: no previous manifest to carry approvals from.
  }
  return null;
}

/**
 * Resolve the human-review status for one asset.
 *
 * A carried-forward approval must satisfy two conditions: a human set it, and the
 * playback bytes it referred to are byte-identical to the ones there now.
 */
function humanReviewFor(spec, current, previous) {
  const prior = previous?.assets?.find((entry) => entry.id === spec.id);
  const priorStatus = prior?.humanReviewStatus;
  const sameBytes = Boolean(prior?.playbackChecksum && current.playback.sha256
    && prior.playbackChecksum === current.playback.sha256);

  if (HUMAN_VALUES.has(priorStatus) && priorStatus !== 'pending' && sameBytes) {
    return {
      status: priorStatus,
      reason: prior.humanReview?.reason || null,
      carriedForward: true,
      note: `Carried forward from the previous manifest: the playback file is byte-identical (sha256 ${current.playback.sha256.slice(0, 16)}…).`,
    };
  }

  if (priorStatus && priorStatus !== 'pending' && !sameBytes) {
    return {
      status: 'pending',
      reason: null,
      carriedForward: false,
      note: 'A previous approval/rejection existed for different bytes. This file has not been listened to, so the review status was reset to pending.',
    };
  }

  return {
    status: 'pending',
    reason: null,
    carriedForward: false,
    note: spec.language === 'bn'
      ? 'Bangla pronunciation and intonation must be confirmed by a native or fluent speaker before demo use.'
      : 'English pronunciation, pace and loudness must be confirmed by listening before demo use.',
  };
}

/** Content status shown to any consumer, independent of the technical verdict. */
function contentStatusFor(evaluation) {
  const { spec, masterSilent } = evaluation;
  if (spec.contentExpectation === 'missing-content') return 'missing-recording';
  if (spec.contentExpectation === 'intentional-pause') return 'intentional-pause';
  if (masterSilent) return 'silent-but-words-expected';
  return 'speech';
}

/** Provenance of the source file a master was derived from. */
function originFor(spec, backupRecord, standardisationRecord) {
  const recorded = standardisationRecord?.assets?.[spec.id];
  if (recorded) return recorded.origin || null;

  const playbackRel = spec.playbackFile;
  const masterRel = spec.masterFile;
  const candidates = [
    playbackRel.replace(/\.mp3$/i, '.m4a'),
    playbackRel,
    masterRel,
  ];
  for (const rel of candidates) {
    const fact = backupRecord?.files?.[rel];
    if (fact) {
      return {
        file: rel,
        backupFile: fact.backupRelativePath,
        sha256: fact.sha256,
        bytes: fact.bytes,
        format: fact.format,
        codec: fact.codec,
        sampleRate: fact.sampleRate,
        channels: fact.channels,
        durationSeconds: fact.durationSeconds,
        preserved: true,
      };
    }
  }
  return null;
}

/** Read the standardisation record, tolerating absence. */
export function readStandardisationRecord(recordPath) {
  const target = recordPath || STANDARDISATION_RECORD_PATH;
  try {
    const parsed = JSON.parse(fs.readFileSync(target, 'utf8'));
    if (parsed && typeof parsed === 'object' && parsed.assets && typeof parsed.assets === 'object') return parsed;
  } catch {
    // Absent before the first conversion run; the manifest still works without it.
  }
  return null;
}

/**
 * Build the whole manifest.
 *
 * @param {{previous?: object|null, backupRecord?: object, standardisationRecord?: object|null,
 *   now?: Date}} [options]
 */
export function buildStandardisedManifest(options = {}) {
  const now = options.now || new Date();
  const previous = options.previous === undefined ? readPreviousManifest() : options.previous;
  const backupRecord = options.backupRecord || readBackupRecord();
  const standardisation = options.standardisationRecord === undefined
    ? readStandardisationRecord()
    : options.standardisationRecord;

  const assets = ASSET_SPECS.map((spec) => {
    const evaluation = evaluateAsset(spec);
    const human = humanReviewFor(spec, evaluation, previous);
    const master = evaluation.master;
    const playback = evaluation.playback;

    return {
      id: spec.id,
      language: spec.language,
      category: spec.category,
      spokenText: spec.spokenText,
      required: spec.required,
      usage: spec.usage,

      masterFile: spec.masterFile,
      playbackFile: spec.playbackFile,
      masterChecksum: master.sha256,
      playbackChecksum: playback.sha256,
      masterFormat: master.exists ? describeMasterFormat() : null,
      playbackFormat: playback.exists ? describePlaybackFormat() : null,
      sampleRate: master.probe?.sampleRate ?? null,
      channels: master.probe?.channels ?? null,
      durationSeconds: master.probe?.durationSeconds ?? null,
      masterBytes: master.exists ? master.bytes : null,
      playbackBytes: playback.exists ? playback.bytes : null,

      technicalValidationStatus: evaluation.technicalValidationStatus,
      technicalProblems: evaluation.problems,
      humanReviewStatus: human.status,

      contentStatus: contentStatusFor(evaluation),
      contentIssue: spec.contentIssue ? spec.contentIssue.detail : null,
      notes: contentNotesFor(spec, evaluation, playback),

      spokenTextNote: spec.recordedSpokenText === spec.spokenText
        ? null
        : `Recorded from ${JSON.stringify(spec.recordedSpokenText)} — a declared deviation from the catalogue cell ${JSON.stringify(spec.spokenText)} (see catalogue.mjs SPOKEN_TEXT_OVERRIDES).`,
      origin: originFor(spec, backupRecord, standardisation),
      playbackDerivation: standardisation?.assets?.[spec.id]?.playbackDerivation || null,

      humanReview: {
        required: true,
        status: human.status,
        carriedForward: human.carriedForward,
        reason: human.reason || human.note,
      },
    };
  });
  const manifest = summariseStandardisedManifest(assets, { now, previous, backupRecord });
  return manifest;
}


/**
 * Wrap the per-asset rows in the document envelope and counts.
 *
 * @param {object[]} assets
 * @param {{now: Date, previous: object|null, backupRecord: object}} context
 */
function summariseStandardisedManifest(assets, context) {
  const count = (predicate) => assets.filter(predicate).length;
  const technicalPass = count((asset) => asset.technicalValidationStatus === 'pass');
  const humanPending = count((asset) => asset.humanReviewStatus === 'pending');
  const tooling = detectDecoder();

  return {
    version: '2.0',
    schema: MANIFEST_SCHEMA,
    generatedAt: context.now.toISOString(),
    locales: ['en', 'bn'],

    formats: {
      master: { ...MASTER_FORMAT, description: describeMasterFormat() },
      playback: { ...PLAYBACK_FORMAT, description: describePlaybackFormat() },
    },

    tool: {
      ffmpeg: tooling.ffmpeg ? tooling.ffmpeg.version : null,
      ffprobe: tooling.ffprobe ? tooling.ffprobe.version : null,
      standardisationUtility: 'scripts/que-006-audio/standardise-audio.mjs',
      validator: 'scripts/que-006-audio/validate-audio-assets.mjs',
    },

    catalogue: {
      document: CATALOGUE_DOC,
      version: CATALOGUE_VERSION,
      assetCount: CATALOGUE_ASSET_COUNT,
      languages: ['en', 'bn'],
    },

    // Generation provenance is carried forward verbatim: the standardisation pass
    // did not regenerate any speech and must not appear to have done so.
    generator: context.previous?.generator || null,

    backup: {
      location: 'frontend/.audio-originals-backup',
      record: 'frontend/.audio-originals-backup/ORIGINALS.json',
      recordedOriginals: Object.keys(context.backupRecord.files || {}).length,
      note: 'Original recordings are preserved byte-for-byte outside public/ before any conversion.',
    },

    summary: {
      total: assets.length,
      masterPresent: count((asset) => asset.masterBytes !== null),
      playbackPresent: count((asset) => asset.playbackBytes !== null),
      technicalPass,
      technicalMissing: count((asset) => asset.technicalValidationStatus === 'missing'),
      technicalFail: count((asset) => asset.technicalValidationStatus === 'fail'),
      contentIssues: count((asset) => asset.contentStatus === 'missing-recording'
        || asset.contentStatus === 'silent-but-words-expected'),
      humanApproved: count((asset) => asset.humanReviewStatus === 'approved'),
      humanPending,
      complete: technicalPass === assets.length,
    },

    playable: {
      readyForPlaybackEngine: technicalPass === assets.length,
      integratedWithApplication: false,
      humanReviewOutstanding: humanPending > 0,
      note: 'These files and this manifest are prepared for a prerecorded-audio engine that does not '
        + 'exist yet. The AMSDP frontend still uses browser speechSynthesis '
        + '(frontend/lib/announcements/speech-synthesis.js is unchanged). Technical validation is not '
        + 'pronunciation approval.',
    },

    assets,
  };
}

/** Notes that must be impossible to miss when a consumer reads the entry. */
function contentNotesFor(spec, evaluation, playback) {
  const notes = [];
  if (spec.contentIssue) notes.push(spec.contentIssue.detail);
  if (spec.contentExpectation === 'intentional-pause') {
    notes.push(`Punctuation-only asset: the catalogue spoken text is ${JSON.stringify(spec.spokenText)}, so `
      + `the file is ${INTENTIONAL_PAUSE_MS} ms of deliberate silence. An engine must insert a pause here, not speak it.`);
  }
  if (evaluation.master.loudness?.ok) {
    notes.push(`Measured master loudness: ${evaluation.master.loudness.detail}.`);
  }
  if (playback.loudness?.ok && !spec.contentIssue) {
    notes.push(`Measured playback loudness: ${playback.loudness.detail}.`);
  }
  return notes.length ? notes : null;
}

/** Write the manifest atomically to the public audio directory. */
export function writeStandardisedManifest(manifest, manifestPath = MANIFEST_PATH) {
  const dir = path.dirname(manifestPath);
  fs.mkdirSync(dir, { recursive: true });
  const temp = path.join(dir, `.${path.basename(manifestPath)}.${process.pid}.tmp`);
  fs.writeFileSync(temp, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  fs.renameSync(temp, manifestPath);
  return manifestPath;
}


