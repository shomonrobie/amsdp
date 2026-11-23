/**
 * QUE-006 — the standardised on-disk audio contract.
 *
 * Every catalogue asset is delivered as two files in `frontend/public/audio/`:
 *
 *   MASTER    PCM WAV, 44.1 kHz, 16-bit, mono — the archive copy of the recording.
 *   PLAYBACK  MP3, 44.1 kHz, mono, 128 kbps CBR — what an audio engine may serve.
 *
 * The master keeps the catalogue filename (`.wav`); the playback file is the same
 * path with `.mp3`. That mapping is derived from `catalogue.mjs`, never typed
 * twice, so a renamed asset cannot silently detach from its audio.
 *
 * This module owns the contract and the measurements. It does not decide what is
 * approved: `contentExpectation` records what the catalogue says *should* be in
 * the file, and the validator reports any asset whose bytes contradict it.
 */

import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

import { ASSETS, PUNCTUATION_ASSET_ID, PUNCTUATION_PAUSE_MS, recordedTextFor } from '../catalogue.mjs';
import { AUDIO_ROOT, REPO_ROOT, WORK_ROOT } from './paths.mjs';
import { detectDecoder, encodeMp3, runAudioTool, transcodeToWav, verifyDecode } from './decode.mjs';

/** Required master format. */
export const MASTER_FORMAT = Object.freeze({
  container: 'wav',
  codec: 'pcm_s16le',
  sampleRate: 44100,
  channels: 1,
  bitDepth: 16,
});

/** Required playback format. */
export const PLAYBACK_FORMAT = Object.freeze({
  container: 'mp3',
  codec: 'mp3',
  sampleRate: 44100,
  channels: 1,
  bitRate: 128000,
  mode: 'cbr',
});

/** Schema id written into manifest.json. */
export const MANIFEST_SCHEMA = 'AMSDP-QUE-006-audio-assets/2.0';

/** Backup of the untouched recordings, deliberately outside `public/`. */
export const BACKUP_ROOT = path.join(REPO_ROOT, 'frontend', '.audio-originals-backup');

/** Record of every preserved original (sizes, hashes, format facts). */
export const BACKUP_RECORD_PATH = path.join(BACKUP_ROOT, 'ORIGINALS.json');

/** Machine record of the standardisation pass (source -> master -> playback). */
export const STANDARDISATION_RECORD_PATH = path.join(WORK_ROOT, 'standardisation.json');

/** A clip shorter than this cannot contain a word; treat it as broken. */
export const MIN_DURATION_SECONDS = 0.05;

/**
 * Content expectation per asset, taken from the catalogue document.
 *
 *   speech             the catalogue names real words; silence is a defect
 *   intentional-pause  the catalogue spoken text is punctuation only
 *   missing-content    the catalogue names words but no recording exists
 *
 * `bn.phrase.room-locative` was declared `missing-content` from 2026-11-20 until
 * 2026-11-21, when the recording `bn/phrase/room-locative.mpeg` was supplied. It is
 * an ordinary speech asset again; that history lives in the standardisation report,
 * not in this table, because the table must describe the tree as it is now.
 */
const CONTENT_EXPECTATION_BY_ID = Object.freeze({
  [PUNCTUATION_ASSET_ID]: 'intentional-pause',
});

/**
 * Assets whose current file is a known placeholder, with the evidence.
 *
 * Empty since 2026-11-21: the single entry (the Bangla locative suffix, which had no
 * recording — the file in `bn/phrase/` was byte-identical to the English silence
 * placeholder) was resolved by supplying `bn/phrase/room-locative.mpeg`. The
 * placeholder itself was never renamed into a speech slot and is still on disk,
 * unreferenced by the catalogue — see the standardisation report's open item O-7.
 */
export const CONTENT_ISSUES = Object.freeze({});

/**
 * The 28 asset specifications in standardised form.
 *
 * `originalFor()` resolves the source file on demand so a lost original is
 * reported instead of silently re-encoded from an already-converted master.
 */
export const ASSET_SPECS = Object.freeze(ASSETS.map((asset) => {
  const masterFile = asset.filename;
  const playbackFile = masterFile.replace(/\.wav$/i, '.mp3');
  return Object.freeze({
    id: asset.id,
    language: asset.language,
    category: asset.category,
    spokenText: asset.spokenText,
    recordedSpokenText: recordedTextFor(asset),
    required: asset.required,
    usage: asset.usage,
    masterFile,
    playbackFile,
    synthetic: asset.synthetic || null,
    contentExpectation: CONTENT_EXPECTATION_BY_ID[asset.id] || 'speech',
    contentIssue: CONTENT_ISSUES[asset.id] || null,
  });
}));

/** @typedef {typeof ASSET_SPECS[number]} AssetSpec */

/** @type {Map<string, AssetSpec>} */
export const SPEC_BY_ID = new Map(ASSET_SPECS.map((spec) => [spec.id, spec]));

/** Playback pause an intentional-pause asset stands for, in milliseconds. */
export const INTENTIONAL_PAUSE_MS = PUNCTUATION_PAUSE_MS;

/** Absolute path of an asset's master file. */
export function masterPath(spec) {
  return path.join(AUDIO_ROOT, ...spec.masterFile.split('/'));
}

/** Absolute path of an asset's playback file. */
export function playbackPath(spec) {
  return path.join(AUDIO_ROOT, ...spec.playbackFile.split('/'));
}

/**
 * Recordings whose file name does not follow the `.m4a` / `.mp3` pattern.
 *
 * `bn/phrase/room-locative.mpeg` carries an MP3 stream despite its `.mpeg`
 * extension, and it is the *recording*, not a derived file. It is named explicitly
 * so `originalFor()` prefers it over the `room-locative.mp3` this utility writes:
 * deriving a master from our own 128 kbps playback would be a needless second
 * lossy generation, and it would leave the master untraceable to its source.
 */
const ORIGINAL_SOURCE_BY_ID = Object.freeze({
  'bn.phrase.room-locative': Object.freeze({
    file: 'bn/phrase/room-locative.mpeg',
    role: 'original-mpeg',
  }),
});

/**
 * Every path a master may legitimately be derived from, most authoritative first.
 *
 * The `.wav` comes last on purpose: after a pass it holds our own converted master,
 * so re-deriving from it would hide the fact that nothing was re-derived.
 *
 * @param {AssetSpec} spec
 * @returns {{rel: string, role: 'original-mpeg'|'original-m4a'|'original-mp3'|'original-wav'}[]}
 */
export function originalCandidatesFor(spec) {
  const recorded = ORIGINAL_SOURCE_BY_ID[spec.id];
  return [
    ...(recorded ? [{ rel: recorded.file, role: recorded.role }] : []),
    { rel: spec.playbackFile.replace(/\.mp3$/i, '.m4a'), role: 'original-m4a' },
    { rel: spec.playbackFile, role: 'original-mp3' },
    { rel: spec.masterFile, role: 'original-wav' },
  ];
}

/**
 * The file a master must be derived from, or `null` when no usable original exists.
 *
 * English assets were generated straight to MP3, so the MP3 *is* the recording.
 * Bangla assets were generated to M4A, and the one hand-supplied Bangla clip arrived
 * as `.mpeg`. An asset declared `missing-content` returns `null` by definition, so a
 * placeholder can never be promoted into a master.
 *
 * @param {AssetSpec} spec
 * @returns {{path: string, rel: string, role: string}|null}
 */
export function originalFor(spec) {
  if (spec.contentExpectation === 'missing-content') return null;
  for (const candidate of originalCandidatesFor(spec)) {
    const abs = path.join(AUDIO_ROOT, ...candidate.rel.split('/'));
    if (fs.existsSync(abs)) return { path: abs, rel: candidate.rel, role: candidate.role };
  }
  return null;
}

/** SHA-256 of a file, lowercase hex. */
export function sha256File(filePath) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

/** Existence, size, hash and mtime of a file, without throwing on absence. */
export function fileFact(filePath) {
  try {
    const stat = fs.statSync(filePath);
    return {
      exists: true,
      bytes: stat.size,
      sha256: sha256File(filePath),
      modifiedAt: new Date(stat.mtimeMs).toISOString(),
    };
  } catch {
    return { exists: false, bytes: 0, sha256: null, modifiedAt: null };
  }
}

/**
 * Everything the standardisation cares about in one ffprobe call, plus per-frame
 * bit rates.
 *
 * The frame sizes are what make a CBR claim checkable: at 44.1 kHz a 128 kbps
 * MPEG-1 Layer III frame is 417 or 418 bytes (the padding bit alternates), so a
 * true CBR file yields a spread of ~0.1 kbps while a VBR file spreads widely.
 *
 * @param {string} filePath
 */
export function probeAudio(filePath) {
  const tooling = detectDecoder();
  const empty = {
    ok: false, formatName: null, codecName: null, sampleRate: null, channels: null,
    bitsPerSample: null, durationSeconds: null, bitRate: null, frameBitRatesKbps: [],
    frameSpreadKbps: null, detail: 'ffprobe unavailable',
  };
  if (!tooling.ffprobe) return empty;

  const result = runAudioTool(tooling.ffprobe.exe, [
    '-v', 'error',
    '-select_streams', 'a:0',
    '-show_entries', 'stream=codec_name,sample_rate,channels,bits_per_sample,bit_rate,duration:format=duration,format_name,bit_rate',
    '-of', 'json',
    filePath,
  ]);
  if (!result.ok) {
    const why = result.stderr.trim().slice(0, 300) || `exit ${result.status}`;
    return { ...empty, detail: `ffprobe failed: ${why}` };
  }

  let parsed;
  try {
    parsed = JSON.parse(result.stdout);
  } catch {
    return { ...empty, detail: 'ffprobe output was not JSON' };
  }
  const stream = (parsed.streams || [])[0];
  if (!stream) return { ...empty, detail: 'ffprobe found no audio stream' };

  const streamSeconds = Number(stream.duration);
  const formatSeconds = Number(parsed.format?.duration);
  const seconds = Number.isFinite(streamSeconds) && streamSeconds > 0 ? streamSeconds
    : (Number.isFinite(formatSeconds) && formatSeconds > 0 ? formatSeconds : null);

  const formatName = parsed.format?.format_name || null;
  const isMp3 = typeof formatName === 'string' && formatName.split(',').includes('mp3');
  const sampleRate = stream.sample_rate ? Number(stream.sample_rate) : null;

  let frameBitRatesKbps = [];
  if (isMp3 && sampleRate) {
    const frames = runAudioTool(tooling.ffprobe.exe, [
      '-v', 'error', '-select_streams', 'a:0',
      '-show_entries', 'frame=pkt_size', '-of', 'csv=p=0', filePath,
    ]);
    if (frames.ok) {
      frameBitRatesKbps = frames.stdout.split(/\r?\n/)
        .map((line) => Number(line.trim().replace(/,$/, '')))
        .filter((size) => Number.isFinite(size) && size > 0)
        // MPEG-1 Layer III: 1152 samples per frame.
        .map((size) => Math.round(((size * 8 * sampleRate) / (1152 * 1000)) * 10) / 10);
    }
  }
  const frameSpreadKbps = frameBitRatesKbps.length
    ? Math.round((Math.max(...frameBitRatesKbps) - Math.min(...frameBitRatesKbps)) * 10) / 10
    : null;

  return {
    ok: true,
    formatName,
    codecName: stream.codec_name || null,
    sampleRate,
    channels: typeof stream.channels === 'number' ? stream.channels : null,
    bitsPerSample: typeof stream.bits_per_sample === 'number' && stream.bits_per_sample > 0
      ? stream.bits_per_sample : null,
    durationSeconds: seconds === null ? null : Math.round(seconds * 1000) / 1000,
    bitRate: stream.bit_rate ? Number(stream.bit_rate) : null,
    frameBitRatesKbps,
    frameSpreadKbps,
    detail: `ffprobe ${tooling.ffprobe.version} read ${stream.codec_name || 'audio'}`,
  };
}

/**
 * Measured loudness of a file, used as objective evidence that a clip contains
 * sound at all. `-91.0 dB` is ffmpeg's value for pure digital silence.
 *
 * This measures; it never normalises. The standardisation must not alter levels.
 *
 * @param {string} filePath
 * @returns {{ok: boolean, meanDb: number|null, maxDb: number|null, detail: string}}
 */
export function measureLoudness(filePath) {
  const tooling = detectDecoder();
  if (!tooling.ffmpeg) {
    return { ok: false, meanDb: null, maxDb: null, detail: 'ffmpeg unavailable — loudness not measured' };
  }
  const result = runAudioTool(tooling.ffmpeg.exe, [
    '-hide_banner', '-nostdin', '-i', filePath,
    '-af', 'volumedetect', '-f', 'null', process.platform === 'win32' ? 'NUL' : '/dev/null',
  ]);
  const text = `${result.stderr}`;
  const mean = /mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB/.exec(text);
  const max = /max_volume:\s*(-?\d+(?:\.\d+)?)\s*dB/.exec(text);
  if (!mean) return { ok: false, meanDb: null, maxDb: null, detail: 'volumedetect produced no reading' };
  return {
    ok: true,
    meanDb: Number(mean[1]),
    maxDb: max ? Number(max[1]) : null,
    detail: `mean_volume ${mean[1]} dB${max ? `, max_volume ${max[1]} dB` : ''}`,
  };
}

/** True when a probe describes the required master format exactly. */
export function masterMatchesContract(probe) {
  return Boolean(probe.ok
    && typeof probe.formatName === 'string' && probe.formatName.split(',').includes('wav')
    && probe.codecName === MASTER_FORMAT.codec
    && probe.sampleRate === MASTER_FORMAT.sampleRate
    && probe.channels === MASTER_FORMAT.channels
    && probe.bitsPerSample === MASTER_FORMAT.bitDepth);
}

/**
 * True when a probe describes the required playback format exactly.
 *
 * CBR is judged by frame-size spread, not by the container's average bit rate: a
 * VBR file can report a 128 kbps average while its frames swing between 96 and
 * 192 kbps. A 0.1–0.2 kbps spread is the padding bit flipping, which is CBR.
 */
export function playbackMatchesContract(probe) {
  return Boolean(probe.ok
    && typeof probe.formatName === 'string' && probe.formatName.split(',').includes('mp3')
    && probe.codecName === 'mp3'
    && probe.sampleRate === PLAYBACK_FORMAT.sampleRate
    && probe.channels === PLAYBACK_FORMAT.channels
    && (probe.bitRate === null || Math.abs(probe.bitRate - PLAYBACK_FORMAT.bitRate) <= 1000)
    && probe.frameSpreadKbps !== null && probe.frameSpreadKbps <= 1);
}

/** Create the parent directory of a file. */
export function ensureParent(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

/**
 * Run a producer that must never read and write the same path.
 *
 * ffmpeg 9.x refuses `-i x.wav ... x.wav` ("Output ... same as Input"), and even
 * if it allowed it, a mid-write failure would destroy the only copy. When the
 * target is the source, the output goes to a sibling temporary file which is
 * verified against the contract *before* it replaces the original; a bad
 * conversion is discarded and the original keeps its bytes.
 *
 * @param {{sourcePath: string, targetPath: string, produce: (outputPath: string) => object,
 *   matches: (probe: object) => boolean, command: string, label: string}} input
 */
function produceSafely(input) {
  const { sourcePath, targetPath, produce, matches, command, label } = input;
  ensureParent(targetPath);
  const inPlace = path.resolve(sourcePath) === path.resolve(targetPath);
  const outputPath = inPlace ? `${targetPath}.${process.pid}.tmp` : targetPath;

  const result = produce(outputPath);
  if (!result.ok) {
    safeUnlink(inPlace ? outputPath : null);
    return { ...result, command };
  }
  if (!inPlace) return { ...result, command };

  const probe = probeAudio(outputPath);
  if (!matches(probe)) {
    safeUnlink(outputPath);
    return {
      ok: false,
      detail: `${label} written to a temporary file did not match the contract (${probe.detail}); `
        + 'the original file was left untouched',
      toolVersion: result.toolVersion || null,
      command,
    };
  }
  fs.renameSync(outputPath, targetPath);
  return { ...result, command, replacedInPlace: true };
}

/** Delete a file if it exists, ignoring errors — used only for temporary files. */
function safeUnlink(filePath) {
  if (!filePath) return;
  try {
    fs.unlinkSync(filePath);
  } catch {
    // Nothing to clean up, or it is already gone.
  }
}

/**
 * Write one master: decode/resample the original to 44.1 kHz 16-bit mono PCM WAV.
 *
 * @param {string} sourcePath
 * @param {string} targetPath
 */
export function writeMaster(sourcePath, targetPath) {
  return produceSafely({
    sourcePath,
    targetPath,
    label: 'master',
    matches: masterMatchesContract,
    command: `ffmpeg -i ${sourcePath} -ac 1 -ar 44100 -c:a pcm_s16le -f wav ${targetPath}`,
    produce: (outputPath) => transcodeToWav(sourcePath, outputPath, {
      channels: MASTER_FORMAT.channels,
      sampleRate: MASTER_FORMAT.sampleRate,
    }),
  });
}

/**
 * Write one playback file from an already-validated master.
 *
 * @param {string} masterFilePath
 * @param {string} targetPath
 */
export function writePlayback(masterFilePath, targetPath) {
  return produceSafely({
    sourcePath: masterFilePath,
    targetPath,
    label: 'playback',
    matches: playbackMatchesContract,
    command: `ffmpeg -i ${masterFilePath} -ar 44100 -ac 1 -c:a libmp3lame -b:a 128k -f mp3 ${targetPath}`,
    produce: (outputPath) => encodeMp3(masterFilePath, outputPath, {
      sampleRate: PLAYBACK_FORMAT.sampleRate,
      channels: PLAYBACK_FORMAT.channels,
      bitRate: PLAYBACK_FORMAT.bitRate,
    }),
  });
}

/** One-line description of the master format, for the manifest and reports. */
export function describeMasterFormat() {
  return `${MASTER_FORMAT.container}/${MASTER_FORMAT.codec}/${MASTER_FORMAT.sampleRate}Hz/mono/${MASTER_FORMAT.bitDepth}-bit`;
}

/** One-line description of the playback format, for the manifest and reports. */
export function describePlaybackFormat() {
  return `${PLAYBACK_FORMAT.container}/${PLAYBACK_FORMAT.sampleRate}Hz/mono/${Math.round(PLAYBACK_FORMAT.bitRate / 1000)}kbps/${PLAYBACK_FORMAT.mode}`;
}

/** Digital silence threshold in dB, as ffmpeg's volumedetect reports it. */
const SILENCE_DB = -90;

/**
 * Inspect one delivery file end to end.
 *
 * @param {string} filePath
 * @param {'master'|'playback'} kind
 */
function inspectDeliveryFile(filePath, kind) {
  const fact = fileFact(filePath);
  if (!fact.exists) {
    return {
      path: filePath, exists: false, bytes: 0, sha256: null,
      probe: null, contractOk: false, decode: null, loudness: null, problems: ['file does not exist'],
    };
  }

  const problems = [];
  if (fact.bytes === 0) problems.push('file is empty');

  const probe = probeAudio(filePath);
  if (!probe.ok) {
    problems.push(`ffprobe cannot read the file: ${probe.detail}`);
    return { path: filePath, ...fact, probe, contractOk: false, decode: null, loudness: null, problems };
  }

  const contractOk = kind === 'master' ? masterMatchesContract(probe) : playbackMatchesContract(probe);
  if (kind === 'master') {
    if (!masterMatchesContract(probe)) {
      problems.push(`master is ${probe.formatName}/${probe.codecName} ${probe.sampleRate}Hz `
        + `${probe.channels}ch ${probe.bitsPerSample ?? '?'}bit; `
        + `expected ${MASTER_FORMAT.codec} ${MASTER_FORMAT.sampleRate}Hz mono ${MASTER_FORMAT.bitDepth}bit`);
    }
  } else if (!playbackMatchesContract(probe)) {
    problems.push(`playback is ${probe.formatName}/${probe.codecName} ${probe.sampleRate}Hz `
      + `${probe.channels}ch ${probe.bitRate ?? '?'}bps spread ${probe.frameSpreadKbps ?? '?'}kbps; `
      + `expected mp3 ${PLAYBACK_FORMAT.sampleRate}Hz mono ${PLAYBACK_FORMAT.bitRate}bps CBR`);
  }

  if (probe.durationSeconds === null) problems.push('duration is unknown');
  else if (probe.durationSeconds < MIN_DURATION_SECONDS) problems.push(`duration ${probe.durationSeconds}s is below the ${MIN_DURATION_SECONDS}s floor`);

  const decode = verifyDecode(filePath);
  if (!decode.verified) problems.push(`decoder check failed: ${decode.detail}`);

  const loudness = measureLoudness(filePath);

  return { path: filePath, ...fact, probe, contractOk, decode, loudness, problems };
}

/**
 * Judge one asset from the bytes on disk.
 *
 * This is the single place where per-asset technical status is decided; the
 * manifest writer and the validator both read it, so a manifest cannot claim a
 * status the validator would contradict.
 *
 * @param {AssetSpec} spec
 */
export function evaluateAsset(spec) {
  const master = inspectDeliveryFile(masterPath(spec), 'master');
  const playback = inspectDeliveryFile(playbackPath(spec), 'playback');
  const problems = [];

  for (const problem of master.problems) problems.push(`master: ${problem}`);
  for (const problem of playback.problems) problems.push(`playback: ${problem}`);

  const masterSilent = master.loudness?.ok && master.loudness.maxDb !== null && master.loudness.maxDb <= SILENCE_DB;
  if (spec.contentExpectation === 'speech' && masterSilent) {
    problems.push(`master is digitally silent (max_volume ${master.loudness.maxDb} dB) but the catalogue names spoken words`);
  }

  let status;
  if (spec.contentExpectation === 'missing-content' && !master.exists) status = 'missing';
  else if (master.exists && playback.exists && problems.length === 0) status = 'pass';
  else if (!master.exists || !playback.exists) status = 'missing';
  else status = 'fail';

  return {
    spec,
    master,
    playback,
    problems,
    technicalValidationStatus: status,
    masterSilent,
  };
}

// __END__




