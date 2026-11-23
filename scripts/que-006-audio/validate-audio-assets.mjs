#!/usr/bin/env node
/**
 * QUE-006 — validate the standardised audio set against the contract and manifest.
 *
 *   node scripts/que-006-audio/validate-audio-assets.mjs
 *   node scripts/que-006-audio/validate-audio-assets.mjs --mode missing
 *   node scripts/que-006-audio/validate-audio-assets.mjs --mode checksums --json
 *   node scripts/que-006-audio/validate-audio-assets.mjs --allow-missing
 *
 * The twelve required checks, and where each is implemented:
 *
 *    1 all 28 WAV masters exist            per-file, `master.exists`
 *    2 all 28 MP3 playback files exist     per-file, `playback.exists`
 *    3 every file is non-empty             per-file, `bytes > 0`
 *    4 every file decodes in ffmpeg        per-file, full `-f null` decode
 *    5 every file has a valid duration     per-file, `durationSeconds`
 *    6 sample rate and channels correct    per-file, probe vs contract
 *    7 MP3 files are actually MP3          per-file, container + codec
 *    8 WAV files are actually PCM WAV      per-file, container + codec + depth
 *    9 no expected asset is missing        per-asset aggregate
 *   10 no duplicate asset IDs              cross-check, ids and file paths
 *   11 every manifest path resolves        manifest cross-check
 *   12 SHA-256 matches the manifest        manifest cross-check
 *
 * What passing does NOT mean: that a clip says the right words, that the Bangla is
 * pronounced acceptably, or that a human ever listened. `humanReviewStatus` is
 * reported as found and is never upgraded here.
 *
 * Exit codes: 0 all checks pass | 1 check failure(s) | 2 usage error |
 *             3 ffprobe/ffmpeg missing, so the format claims cannot be checked.
 */

import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';

import {
  ASSET_SPECS,
  BACKUP_RECORD_PATH,
  MANIFEST_SCHEMA,
  MASTER_FORMAT,
  PLAYBACK_FORMAT,
  SPEC_BY_ID,
  describeMasterFormat,
  describePlaybackFormat,
  evaluateAsset,
  masterPath,
  playbackPath,
} from './lib/audio-standard.mjs';
import { readBackupRecord } from './lib/audio-backup.mjs';
import { AUDIO_ROOT, MANIFEST_PATH, REPO_ROOT } from './lib/paths.mjs';
import { detectDecoder } from './lib/decode.mjs';

const USAGE = `
QUE-006 audio asset validation

Usage:
  node scripts/que-006-audio/validate-audio-assets.mjs [options]

Options:
  --mode all         every check (default)
  --mode missing     only existence and completeness checks
  --mode checksums   only manifest path resolution and SHA-256 verification
  --allow-missing    report absent files as pending work, not failures
  --json             print the full report as JSON
  --quiet            print failures and the verdict only
  --help, -h         show this help

Exit codes: 0 pass | 1 failure(s) | 2 usage error | 3 ffprobe/ffmpeg missing.
`;

/** @param {string[]} argv */
export function parseArgs(argv) {
  const args = { mode: 'all', allowMissing: false, json: false, quiet: false, help: false };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    switch (arg) {
      case '--mode': {
        const value = argv[index + 1];
        if (!['all', 'missing', 'checksums'].includes(value)) {
          throw new Error(`--mode expects all, missing or checksums (got ${JSON.stringify(value)})`);
        }
        args.mode = value;
        index += 1;
        break;
      }
      case '--allow-missing': args.allowMissing = true; break;
      case '--json': args.json = true; break;
      case '--quiet': args.quiet = true; break;
      case '--help': case '-h': args.help = true; break;
      default: throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}

/** Repository-relative path, forward slashes. */
function rel(absPath) {
  return path.relative(REPO_ROOT, absPath).split(path.sep).join('/');
}

/**
 * The per-file checks (required checks 1–8) for one delivery file.
 *
 * @param {object} spec
 * @param {'master'|'playback'} kind
 * @param {object} file result of `evaluateAsset().master|.playback`
 */
function fileChecks(spec, kind, file) {
  const checks = [];
  const contract = kind === 'master' ? MASTER_FORMAT : PLAYBACK_FORMAT;
  const label = kind === 'master' ? spec.masterFile : spec.playbackFile;
  const add = (id, name, ok, detail) => checks.push({ id, name: `${kind} ${name}`, ok, detail });

  add(kind === 'master' ? '1' : '2', 'file exists', file.exists, label);
  if (!file.exists) return checks;

  add('3', 'file is non-empty', file.bytes > 0, `${file.bytes} bytes`);
  const probe = file.probe || {};

  if (kind === 'master') {
    add('8', 'file is PCM WAV', file.contractOk,
      `${probe.formatName}/${probe.codecName} ${probe.sampleRate}Hz ${probe.channels}ch ${probe.bitsPerSample}bit`
      + ` — required ${describeMasterFormat()}`);
  } else {
    add('7', 'file is MP3', file.contractOk,
      `${probe.formatName}/${probe.codecName} ${probe.sampleRate}Hz ${probe.channels}ch `
      + `${probe.bitRate}bps frame spread ${probe.frameSpreadKbps}kbps — required ${describePlaybackFormat()}`);
  }

  add('6', 'sample rate and channels', probe.sampleRate === contract.sampleRate && probe.channels === contract.channels,
    `${probe.sampleRate}Hz ${probe.channels}ch — required ${contract.sampleRate}Hz ${contract.channels}ch`);

  add('5', 'valid duration',
    typeof probe.durationSeconds === 'number' && probe.durationSeconds > 0,
    probe.durationSeconds === null ? 'no duration reported' : `${probe.durationSeconds}s`);

  add('4', 'decodes in ffmpeg', Boolean(file.decode?.verified),
    file.decode ? `${file.decode.method}: ${file.decode.detail}` : 'decode not attempted');

  return checks;
}

/** Cross-file checks: duplicate IDs, duplicate output paths, duplicate audio. */
function crossFileChecks(evaluations) {
  const checks = [];
  const ids = ASSET_SPECS.map((spec) => spec.id);
  const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index);
  checks.push({
    id: '10', name: 'no duplicate asset IDs', ok: duplicateIds.length === 0,
    detail: duplicateIds.length ? `repeated ids: ${[...new Set(duplicateIds)].join(', ')}` : `${ids.length} unique ids`,
  });

  const paths = ASSET_SPECS.flatMap((spec) => [spec.masterFile, spec.playbackFile]);
  const duplicatePaths = paths.filter((candidate, index) => paths.indexOf(candidate) !== index);
  checks.push({
    id: '10', name: 'no duplicate output paths', ok: duplicatePaths.length === 0,
    detail: duplicatePaths.length ? `repeated paths: ${[...new Set(duplicatePaths)].join(', ')}` : `${paths.length} unique paths`,
  });

  // Different sentences must not share bytes: a real provider failure mode, and the
  // check that exposes a placeholder copied into a slot that expects speech.
  const byHash = new Map();
  for (const evaluation of evaluations) {
    const hash = evaluation.master.sha256;
    if (!hash || evaluation.spec.contentExpectation !== 'speech') continue;
    if (!byHash.has(hash)) byHash.set(hash, []);
    byHash.get(hash).push(evaluation.spec.id);
  }
  const duplicates = [...byHash.entries()].filter(([, group]) => group.length > 1);
  checks.push({
    id: '10', name: 'no two speech assets share identical bytes', ok: duplicates.length === 0,
    detail: duplicates.length
      ? duplicates.map(([hash, group]) => `${group.join(' = ')} (sha256 ${hash.slice(0, 16)}…)`).join('; ')
      : `${byHash.size} speech assets, all byte-distinct`,
  });

  return checks;
}

/**
 * Required checks 11 and 12, plus the manifest's agreement with the disk.
 *
 * @param {Array<{spec: object, master: object, playback: object, technicalValidationStatus: string}>} evaluations
 */
function manifestChecks(evaluations) {
  const checks = [];
  const failures = [];
  const warn = (id, name, detail) => checks.push({ id, name, ok: true, warn: true, detail });
  const add = (id, name, ok, detail) => {
    checks.push({ id, name, ok, detail });
    if (!ok) failures.push(name);
  };

  if (!fs.existsSync(MANIFEST_PATH)) {
    add('11', 'manifest exists', false, `absent at ${rel(MANIFEST_PATH)} — run rebuild-audio-manifest.mjs`);
    return { checks, failures };
  }

  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
  } catch (err) {
    add('11', 'manifest parses as JSON', false, err.message);
    return { checks, failures };
  }

  if (manifest.schema !== MANIFEST_SCHEMA) {
    warn('11', 'manifest schema', `${manifest.schema || 'unversioned'} — expected ${MANIFEST_SCHEMA}; rebuild it`);
  }
  add('11', 'manifest declares the catalogue size', (manifest.assets || []).length === ASSET_SPECS.length,
    `${(manifest.assets || []).length} entries — expected ${ASSET_SPECS.length}`);

  const byId = new Map((manifest.assets || []).map((entry) => [entry.id, entry]));
  const manifestIds = [...byId.keys()];
  const missingFromManifest = ASSET_SPECS.filter((spec) => !byId.has(spec.id)).map((spec) => spec.id);
  const extraInManifest = manifestIds.filter((id) => !SPEC_BY_ID.has(id));
  add('11', 'manifest covers every catalogue asset', missingFromManifest.length === 0 && extraInManifest.length === 0,
    `missing: ${missingFromManifest.join(', ') || 'none'}; not in catalogue: ${extraInManifest.join(', ') || 'none'}`);

  const unresolvable = [];
  const checksumMismatch = [];
  const wordingDrift = [];
  const statusDrift = [];
  const badHumanStatus = [];

  for (const evaluation of evaluations) {
    const spec = evaluation.spec;
    const entry = byId.get(spec.id);
    if (!entry) continue;

    for (const key of ['masterFile', 'playbackFile']) {
      const value = entry[key];
      if (typeof value !== 'string' || !value) {
        unresolvable.push(`${spec.id}.${key} is ${JSON.stringify(value)}`);
        continue;
      }
      const abs = path.resolve(AUDIO_ROOT, ...value.split('/'));
      if (!abs.startsWith(AUDIO_ROOT)) {
        unresolvable.push(`${spec.id}.${key} points outside the audio directory (${value})`);
        continue;
      }
      // A manifest entry that claims the asset is present must point at a real
      // file. An entry recorded as missing still names the path the engine will
      // look for, which is not an overclaim — its absence is reported per asset.
      if (!fs.existsSync(abs) && entry.technicalValidationStatus !== 'missing') {
        unresolvable.push(`${spec.id}.${key} -> ${rel(abs)} is claimed present but does not exist`);
      }
    }

    const actualMaster = evaluation.master.sha256;
    const actualPlayback = evaluation.playback.sha256;
    if (entry.masterChecksum !== actualMaster) {
      checksumMismatch.push(`${spec.id}.masterChecksum ${String(entry.masterChecksum).slice(0, 16)}... vs file ${String(actualMaster).slice(0, 16)}...`);
    }
    if (entry.playbackChecksum !== actualPlayback) {
      checksumMismatch.push(`${spec.id}.playbackChecksum ${String(entry.playbackChecksum).slice(0, 16)}... vs file ${String(actualPlayback).slice(0, 16)}...`);
    }

    if (entry.spokenText !== spec.spokenText) {
      wordingDrift.push(`${spec.id}: manifest ${JSON.stringify(entry.spokenText)} vs catalogue ${JSON.stringify(spec.spokenText)}`);
    }
    if (entry.technicalValidationStatus !== evaluation.technicalValidationStatus) {
      statusDrift.push(`${spec.id}: manifest ${entry.technicalValidationStatus} vs disk ${evaluation.technicalValidationStatus}`);
    }
    if (!['pending', 'approved', 'rejected'].includes(entry.humanReviewStatus)) {
      badHumanStatus.push(`${spec.id}: ${JSON.stringify(entry.humanReviewStatus)}`);
    }
  }

  add('11', 'every manifest path resolves to an existing file', unresolvable.length === 0,
    unresolvable.length ? unresolvable.join('; ') : `${ASSET_SPECS.length * 2} paths resolve under frontend/public/audio/`);

  add('12', 'manifest checksums match the files', checksumMismatch.length === 0,
    checksumMismatch.length ? checksumMismatch.join('; ') : `${ASSET_SPECS.length * 2} SHA-256 values verified`);

  add('12', 'manifest statuses match the files', statusDrift.length === 0,
    statusDrift.length ? statusDrift.join('; ') : 'every technicalValidationStatus matches a fresh evaluation');

  add('12', 'manifest spoken text matches the catalogue', wordingDrift.length === 0,
    wordingDrift.length ? wordingDrift.join('; ') : 'every spokenText is the catalogue value verbatim');

  add('12', 'human review status is a known value', badHumanStatus.length === 0,
    badHumanStatus.length ? badHumanStatus.join('; ') : 'every humanReviewStatus is pending, approved or rejected');

  const honest = (manifest.playable || {}).integratedWithApplication === false;
  add('11', 'manifest claims no application integration', honest,
    honest
      ? 'integratedWithApplication=false — the frontend does not play these files yet'
      : 'integratedWithApplication is not false — the manifest would overclaim playback');

  return { checks, failures };
}

/**
 * Provenance group: the backup that protects every original still verifies.
 *
 * Not one of the twelve required checks, but without it "the originals are
 * preserved" would be an unverified claim.
 */
function backupChecks() {
  const checks = [];
  if (!fs.existsSync(BACKUP_RECORD_PATH)) {
    checks.push({
      id: 'P', name: 'original backup record exists', ok: false,
      detail: 'absent at frontend/.audio-originals-backup/ORIGINALS.json'
        + ' — run standardise-audio.mjs to preserve the originals',
    });
    return checks;
  }

  const record = readBackupRecord();
  const entries = Object.entries(record.files || {});
  const broken = [];
  for (const [relPath, fact] of entries) {
    const abs = path.join(path.dirname(BACKUP_RECORD_PATH), ...relPath.split('/'));
    if (!fs.existsSync(abs)) {
      broken.push(`${relPath}: backup copy missing`);
      continue;
    }
    if (fact.backupSha256 && fileSha256(abs) !== fact.backupSha256) {
      broken.push(`${relPath}: backup copy no longer matches its recorded hash`);
    }
  }
  checks.push({
    id: 'P', name: 'every preserved original still verifies', ok: broken.length === 0,
    detail: broken.length ? broken.join('; ') : `${entries.length} originals recorded and hash-verified`,
  });
  return checks;
}

/**
 * Run the requested validation mode.
 *
 * @param {ReturnType<typeof parseArgs>} args
 */
export function runValidation(args) {
  const decoder = detectDecoder();
  const report = {
    mode: args.mode,
    allowMissing: args.allowMissing,
    verdict: 'pass',
    exitCode: 0,
    reason: '',
    counts: {},
    checks: [],
    assets: [],
    failures: [],
    warnings: [],
    limits: {},
  };

  if (!decoder.ffprobe || !decoder.ffmpeg) {
    report.verdict = 'fail';
    report.exitCode = 3;
    report.reason = 'ffprobe and ffmpeg are both required: without them the format, '
      + 'duration and decodability claims cannot be checked. Nothing was verified.';
    return report;
  }
  report.limits = {
    decoder: `${decoder.ffprobe.version} + ${decoder.ffmpeg.version}`,
    method: 'ffprobe stream facts, per-frame MP3 bit rates, and a full ffmpeg decode of every file',
    verified: 'existence, size, container identity, codec, sample rate, channels, bit depth, '
      + 'duration, CBR frame spread, full decodability, manifest agreement and SHA-256',
    notVerified: 'that a clip speaks the right words, Bangla pronunciation, perceived loudness, '
      + 'suitability of the voice, and any human approval',
  };

  const evaluations = ASSET_SPECS.map((spec) => evaluateAsset(spec));

  // ---- Per-file checks 1-8 -------------------------------------------------
  for (const evaluation of evaluations) {
    const spec = evaluation.spec;
    const checks = [
      ...fileChecks(spec, 'master', evaluation.master),
      ...fileChecks(spec, 'playback', evaluation.playback),
    ];
    const failed = checks.filter((check) => !check.ok);
    const onlyAbsent = failed.length > 0 && failed.every((check) => check.name.endsWith('file exists'));
    const status = failed.length === 0 ? 'pass'
      : (onlyAbsent && args.allowMissing ? 'warn' : 'fail');

    if (status === 'fail') report.failures.push(spec.id);
    if (status === 'warn') report.warnings.push(spec.id);

    report.assets.push({
      id: spec.id,
      language: spec.language,
      contentStatus: evaluation.spec.contentExpectation,
      status,
      master: summariseFile(evaluation.master, 'master'),
      playback: summariseFile(evaluation.playback, 'playback'),
      checks,
      problems: evaluation.problems,
    });
  }

  // ---- Cross-file and manifest checks -------------------------------------
  if (args.mode === 'all') {
    const cross = crossFileChecks(evaluations);
    report.checks.push(...cross);
    for (const check of cross.filter((candidate) => !candidate.ok)) report.failures.push(`check ${check.id}: ${check.name}`);
  }

  if (args.mode !== 'missing') {
    const manifest = manifestChecks(evaluations);
    report.checks.push(...manifest.checks);
    for (const failure of manifest.failures) report.failures.push(`manifest: ${failure}`);
  }

  for (const check of backupChecks()) {
    report.checks.push(check);
    if (!check.ok) report.failures.push(`provenance: ${check.name}`);
  }

  const masterPresent = evaluations.filter((evaluation) => evaluation.master.exists).length;
  const playbackPresent = evaluations.filter((evaluation) => evaluation.playback.exists).length;
  report.counts = {
    total: ASSET_SPECS.length,
    pass: report.assets.filter((row) => row.status === 'pass').length,
    warn: report.warnings.length,
    fail: report.assets.filter((row) => row.status === 'fail').length,
    masterPresent,
    playbackPresent,
  };

  report.verdict = report.failures.length === 0 ? 'pass' : 'fail';
  report.exitCode = report.verdict === 'pass' ? 0 : 1;
  report.reason = report.verdict === 'pass'
    ? `all ${ASSET_SPECS.length} assets validated: ${masterPresent} masters, ${playbackPresent} playback files`
      + (report.warnings.length ? `; ${report.warnings.length} asset(s) absent and treated as pending work` : '')
    : `${report.failures.length} failing item(s) across ${ASSET_SPECS.length} catalogue assets`;

  return report;
}

/** Compact facts for one file, for the report and the console. */
function summariseFile(file, kind) {
  if (!file.exists) return { exists: false };
  return {
    exists: true,
    bytes: file.bytes,
    sha256: file.sha256,
    format: file.probe?.formatName ?? null,
    codec: file.probe?.codecName ?? null,
    sampleRate: file.probe?.sampleRate ?? null,
    channels: file.probe?.channels ?? null,
    bitsPerSample: file.probe?.bitsPerSample ?? null,
    bitRate: file.probe?.bitRate ?? null,
    frameSpreadKbps: file.probe?.frameSpreadKbps ?? null,
    durationSeconds: file.probe?.durationSeconds ?? null,
    contractOk: file.contractOk,
    decodeVerifiedBy: file.decode?.method ?? 'none',
    loudness: file.loudness?.ok ? { meanDb: file.loudness.meanDb, maxDb: file.loudness.maxDb } : null,
    kind,
  };
}


/** SHA-256 helper kept local so this file never depends on the writer path. */
function fileSha256(filePath) {
  const hash = createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

/** Human-readable report. `quiet` keeps failures and the verdict only. */
function printReport(report, quiet) {
  console.log('QUE-006 audio asset validation');
  console.log(`  mode ${report.mode}${report.allowMissing ? ' (--allow-missing)' : ''} · decoder ${report.limits.decoder || 'none'}`);
  console.log(`  master   ${describeMasterFormat()}`);
  console.log(`  playback ${describePlaybackFormat()}`);
  console.log(`  manifest frontend/public/audio/manifest.json`);

  if (!quiet) {
    console.log('\nFile-level results');
    for (const row of report.assets) {
      const bad = row.checks.filter((check) => !check.ok);
      const mark = row.status === 'pass' ? 'OK  ' : row.status === 'warn' ? 'PEND' : 'FAIL';
      console.log(`  [${mark}] ${row.id}`);
      for (const kind of ['master', 'playback']) {
        const file = row[kind];
        if (!file.exists) {
          console.log(`         ${kind.padEnd(8)} absent`);
          continue;
        }
        const depth = file.bitsPerSample ? ` ${file.bitsPerSample}bit` : '';
        const cbr = kind === 'playback' ? ` CBR spread ${file.frameSpreadKbps}kbps` : '';
        console.log(`         ${kind.padEnd(8)} ${file.codec} ${file.sampleRate}Hz ${file.channels}ch${depth} `
          + `${file.durationSeconds}s ${file.bytes}B base ${(file.bitRate / 1000).toFixed(0)}kbps${cbr} `
          + `sha256 ${String(file.sha256).slice(0, 12)}... decoded by ${file.decodeVerifiedBy}`);
      }
      for (const check of bad) console.log(`         -> check ${check.id} ${check.name}: ${check.detail}`);
    }

    console.log('\nCross-file and manifest checks');
    for (const check of report.checks) {
      const mark = check.ok ? (check.warn ? 'WARN' : 'OK  ') : 'FAIL';
      console.log(`  [${mark}] (${check.id}) ${check.name}`);
      console.log(`         ${check.detail}`);
    }
  }

  if (report.failures.length) {
    console.log('\nFailures');
    for (const failure of report.failures) console.log(`  - ${failure}`);
  }
  if (report.warnings.length) {
    console.log('\nPending (treated as work outstanding, not a pass)');
    for (const warning of report.warnings) console.log(`  - ${warning}`);
  }

  console.log('\nSummary');
  console.log(`  assets ${report.counts.pass}/${report.counts.total} pass · warn ${report.counts.warn} · fail ${report.counts.fail}`
    + ` · masters ${report.counts.masterPresent}/${report.counts.total}`
    + ` · playback ${report.counts.playbackPresent}/${report.counts.total}`);
  console.log(`  verdict ${report.verdict.toUpperCase()} — ${report.reason}`);
  console.log('  not verified: pronunciation, wording by ear, loudness suitability, human approval');
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (err) {
    console.error(`error: ${err.message}`);
    console.error(USAGE);
    process.exit(2);
  }
  if (args.help) {
    console.log(USAGE);
    process.exit(0);
  }
  const report = runValidation(args);
  if (args.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    printReport(report, args.quiet);
  }
  process.exit(report.exitCode);
}




