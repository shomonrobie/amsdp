#!/usr/bin/env node
/**
 * QUE-006 — standardise the audio set to WAV masters + MP3 playback files.
 *
 *   node scripts/que-006-audio/standardise-audio.mjs --dry-run   # show the plan
 *   node scripts/que-006-audio/standardise-audio.mjs             # back up, convert, rebuild manifest
 *   node scripts/que-006-audio/standardise-audio.mjs --backup-only
 *
 * Order of operations, and why:
 *
 *   1. BACK UP every existing recording into `frontend/.audio-originals-backup/`,
 *      re-hashing each copy. Nothing is converted until the copy that protects the
 *      original has been verified.
 *   2. MASTERS. `frontend/public/audio/<lang>/<category>/<name>.wav` at 44.1 kHz,
 *      16-bit, mono PCM, derived from the original recording.
 *   3. PLAYBACK. `<name>.mp3` at 44.1 kHz, mono, 128 kbps CBR, encoded from the
 *      validated master. The one exception is an existing MP3 that is already
 *      exactly that format: it is left byte-identical rather than decoded and
 *      re-encoded, because a second lossy generation can only remove information.
 *   4. MANIFEST rebuilt from what is now on disk.
 *
 * The run is idempotent: a file that already satisfies the contract is skipped, so
 * re-running repairs missing outputs and changes nothing else. Nothing is ever
 * deleted, and no original is overwritten unless a verified backup of it exists.
 *
 * Exit codes: 0 all outputs in place | 1 conversions failed | 2 usage error |
 *             3 ffmpeg missing | 4 backup could not be verified.
 */

import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import {
  ASSET_SPECS,
  BACKUP_ROOT,
  MASTER_FORMAT,
  PLAYBACK_FORMAT,
  STANDARDISATION_RECORD_PATH,
  describeMasterFormat,
  describePlaybackFormat,
  fileFact,
  masterMatchesContract,
  masterPath,
  originalCandidatesFor,
  originalFor,
  playbackMatchesContract,
  playbackPath,
  probeAudio,
  writeMaster,
  writePlayback,
} from './lib/audio-standard.mjs';
import { backupOriginals, readBackupRecord } from './lib/audio-backup.mjs';
import { AUDIO_ROOT } from './lib/paths.mjs';
import { detectDecoder } from './lib/decode.mjs';
import {
  buildStandardisedManifest,
  readPreviousManifest,
  readStandardisationRecord,
  writeStandardisedManifest,
} from './lib/audio-standard-manifest.mjs';

const USAGE = `
QUE-006 audio standardisation — WAV masters + MP3 playback files

Usage:
  node scripts/que-006-audio/standardise-audio.mjs [options]

Options:
  --dry-run         report what would happen; change nothing
  --force           re-derive outputs even when they already satisfy the contract
  --backup-only     copy and verify the originals, then stop
  --no-manifest     convert but do not rewrite manifest.json
  --json            print the run report as JSON
  --quiet           print the summary only
  --help, -h        show this help

Exit codes: 0 outputs in place | 1 conversion failure(s) | 2 usage error |
            3 ffmpeg missing | 4 backup not verifiable.
`;

/** @param {string[]} argv */
export function parseArgs(argv) {
  const args = {
    dryRun: false, force: false, backupOnly: false, writeManifest: true,
    json: false, quiet: false, help: false,
  };
  for (const arg of argv) {
    switch (arg) {
      case '--dry-run': args.dryRun = true; break;
      case '--force': args.force = true; break;
      case '--backup-only': args.backupOnly = true; break;
      case '--no-manifest': args.writeManifest = false; break;
      case '--json': args.json = true; break;
      case '--quiet': args.quiet = true; break;
      case '--help': case '-h': args.help = true; break;
      default: throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}

/**
 * Where a master should be derived from for this run.
 *
 * With `--force`, a verified backup copy is preferred over the file in the tree:
 * after the first pass the in-tree file may already be the converted master, and
 * re-encoding a WAV from a WAV would hide the fact that nothing was re-derived.
 *
 * @param {object} spec
 * @param {object} backupRecord
 * @param {boolean} force
 */
function resolveOriginForConversion(spec, backupRecord, force) {
  const inTree = originalFor(spec);
  if (!force) return inTree ? { ...inTree, fromBackup: false } : null;

  const candidates = spec.contentExpectation === 'missing-content'
    ? []
    : originalCandidatesFor(spec).map((candidate) => candidate.rel);
  for (const rel of candidates) {
    const record = backupRecord.files?.[rel];
    if (!record?.backupSha256) continue;
    const abs = path.join(BACKUP_ROOT, ...rel.split('/'));
    if (!fs.existsSync(abs)) continue;
    if (fileFact(abs).sha256 !== record.backupSha256) continue;
    return { path: abs, role: 'backup-original', fromBackup: true, rel };
  }
  return inTree ? { ...inTree, fromBackup: false } : null;
}

/**
 * Is overwriting this path safe? Only when a verified backup of its current bytes
 * exists. Otherwise an in-place conversion could destroy the only copy.
 *
 * @param {string} relPath path relative to the audio root
 * @param {string} absPath
 * @param {object} backupRecord
 * @param {{dryRun?: boolean}} [options]
 */
function overwriteIsSafe(relPath, absPath, backupRecord, options = {}) {
  if (!fs.existsSync(absPath)) return { safe: true, reason: 'target does not exist yet' };
  const fact = fileFact(absPath);
  const preserved = backupRecord.files?.[relPath];
  if (preserved?.backupSha256 && preserved.backupSha256 === fact.sha256) {
    return { safe: true, reason: `verified backup at frontend/.audio-originals-backup/${relPath}` };
  }
  // In a dry run nothing has been copied yet, so a file that this run would
  // preserve is safe to plan an overwrite for.
  if (options.dryRun && preserved?.status === 'would-copy') {
    return { safe: true, reason: 'a verified backup of this file would be created first' };
  }
  return {
    safe: false,
    reason: `no verified backup matches ${relPath} (sha256 ${String(fact.sha256).slice(0, 16)}...); `
      + 'refusing to overwrite a file that could be the only copy',
  };
}

/**
 * Phase 2 — produce every WAV master.
 *
 * @param {{dryRun: boolean, force: boolean}} args
 * @param {{backupRecord: object}} context
 */
export function ensureMasters(args, context) {
  const rows = [];
  for (const spec of ASSET_SPECS) {
    const target = masterPath(spec);
    const existing = fs.existsSync(target) ? probeAudio(target) : null;
    const valid = Boolean(existing?.ok && masterMatchesContract(existing)
      && existing.durationSeconds !== null && existing.durationSeconds > 0);
    const origin = resolveOriginForConversion(spec, context.backupRecord, args.force);

    /** @type {object} */
    const row = {
      id: spec.id,
      masterFile: spec.masterFile,
      origin: origin ? { path: describeRelative(origin.path), role: origin.role } : null,
      action: null,
      detail: null,
    };

    if (valid && !args.force) {
      row.action = 'kept-valid';
      row.detail = `already ${describeMasterFormat()} (${existing.durationSeconds}s)`;
      rows.push(row);
      continue;
    }

    if (!origin) {
      row.action = spec.contentExpectation === 'missing-content' ? 'declared-missing' : 'missing-original';
      row.detail = spec.contentIssue ? spec.contentIssue.detail
        : 'no original recording exists for this asset, so no master can be derived';
      rows.push(row);
      continue;
    }

    const guard = overwriteIsSafe(spec.masterFile, target, context.backupRecord, { dryRun: args.dryRun });
    if (!guard.safe) {
      row.action = 'refused-no-backup';
      row.detail = guard.reason;
      rows.push(row);
      continue;
    }

    if (args.dryRun) {
      row.action = 'would-convert';
      row.detail = `${describeRelative(origin.path)} -> ${spec.masterFile} (${describeMasterFormat()})`;
      rows.push(row);
      continue;
    }

    const result = writeMaster(origin.path, target);
    if (!result.ok) {
      row.action = 'convert-failed';
      row.detail = result.detail;
      rows.push(row);
      continue;
    }
    const after = probeAudio(target);
    if (!after.ok || !masterMatchesContract(after)) {
      row.action = 'convert-failed';
      row.detail = `ffmpeg wrote the file but it does not match the contract: ${after.detail}`;
      rows.push(row);
      continue;
    }
    row.action = 'converted';
    row.detail = `${describeRelative(origin.path)} -> ${spec.masterFile}; ${after.durationSeconds}s, ${describeMasterFormat()}`;
    rows.push(row);
  }
  return rows;
}

/**
 * Phase 3 — produce every MP3 playback file from its validated master.
 *
 * @param {{dryRun: boolean, force: boolean}} args
 * @param {{backupRecord: object}} context
 * @param {object[]} masterRows output of `ensureMasters`
 */
export function ensurePlayback(args, context, masterRows) {
  const masterState = new Map(masterRows.map((row) => [row.id, row]));
  const rows = [];

  for (const spec of ASSET_SPECS) {
    const target = playbackPath(spec);
    const masterRow = masterState.get(spec.id);
    const masterOk = Boolean(masterRow && (masterRow.action === 'kept-valid'
      || masterRow.action === 'converted' || masterRow.action === 'would-convert'));
    const existing = fs.existsSync(target) ? probeAudio(target) : null;
    const valid = Boolean(existing?.ok && playbackMatchesContract(existing)
      && existing.durationSeconds !== null && existing.durationSeconds > 0);

    const preserved = context.backupRecord.files?.[spec.playbackFile];
    const currentSha = fs.existsSync(target) ? fileFact(target).sha256 : null;
    const isUntouchedOriginal = Boolean(preserved?.sha256 && currentSha && preserved.sha256 === currentSha);

    /** @type {object} */
    const row = { id: spec.id, playbackFile: spec.playbackFile, action: null, detail: null, derivation: null };

    if (valid && !args.force) {
      row.action = 'kept-valid';
      row.derivation = isUntouchedOriginal ? 'original-mp3-preserved' : 'existing-conformant';
      row.detail = `already ${describePlaybackFormat()} (${existing.durationSeconds}s)`
        + (isUntouchedOriginal
          ? '; byte-identical to the preserved original, so it was not re-encoded'
          : '');
      rows.push(row);
      continue;
    }

    if (!masterOk) {
      row.action = 'skipped-no-master';
      row.detail = `master is ${masterRow ? masterRow.action : 'unknown'}, so no playback file can be built from it`;
      rows.push(row);
      continue;
    }

    const guard = overwriteIsSafe(spec.playbackFile, target, context.backupRecord, { dryRun: args.dryRun });
    if (!guard.safe) {
      row.action = 'refused-no-backup';
      row.detail = guard.reason;
      rows.push(row);
      continue;
    }

    if (args.dryRun) {
      row.action = 'would-encode';
      row.derivation = 'encoded-from-master';
      row.detail = `${spec.masterFile} -> ${spec.playbackFile} (${describePlaybackFormat()})`;
      rows.push(row);
      continue;
    }

    const result = writePlayback(masterPath(spec), target);
    if (!result.ok) {
      row.action = 'encode-failed';
      row.detail = result.detail;
      rows.push(row);
      continue;
    }
    const after = probeAudio(target);
    if (!after.ok || !playbackMatchesContract(after)) {
      row.action = 'encode-failed';
      row.detail = `ffmpeg wrote the file but it does not match the contract: ${after.detail}`;
      rows.push(row);
      continue;
    }
    row.action = 'encoded';
    row.derivation = 'encoded-from-master';
    row.detail = `${spec.masterFile} -> ${spec.playbackFile}; ${after.durationSeconds}s, ${describePlaybackFormat()}`;
    rows.push(row);
  }
  return rows;
}

/**
 * Run the whole standardisation: backup, masters, playback, manifest.
 *
 * @param {ReturnType<typeof parseArgs>} args
 */
export function run(args) {
  const tooling = detectDecoder();
  const startedAt = new Date();
  const report = {
    startedAt: startedAt.toISOString(),
    dryRun: args.dryRun,
    tooling: {
      ffmpeg: tooling.ffmpeg ? tooling.ffmpeg.version : null,
      ffprobe: tooling.ffprobe ? tooling.ffprobe.version : null,
    },
    contract: { master: describeMasterFormat(), playback: describePlaybackFormat() },
    backup: null,
    masters: [],
    playback: [],
    manifest: null,
    failures: [],
    gaps: [],
    exitCode: 0,
    reason: '',
  };

  if (!tooling.ffmpeg && !args.dryRun) {
    report.exitCode = 3;
    report.reason = 'ffmpeg is not installed, so no master or playback file can be produced. Nothing was changed.';
    return report;
  }

  // ---- Phase 1: preserve the originals -------------------------------------
  // Delivery paths are files this utility writes; the backup snapshot must not
  // grow to include its own outputs on every re-run.
  const deliveryPaths = new Set(ASSET_SPECS.flatMap((spec) => [spec.masterFile, spec.playbackFile]));
  const backup = backupOriginals({ audioRoot: AUDIO_ROOT, dryRun: args.dryRun, deliveryPaths });
  report.backup = {
    root: 'frontend/.audio-originals-backup',
    record: 'frontend/.audio-originals-backup/ORIGINALS.json',
    counts: backup.counts,
    files: backup.rows.map((row) => ({ rel: row.rel, action: row.action, sha256: row.sha256, note: row.note || null })),
  };

  if (backup.counts.conflict > 0 || backup.counts.copyMismatch > 0 || backup.counts.sourceMissing > 0) {
    report.exitCode = 4;
    report.reason = 'The backup of the originals could not be verified, so nothing was converted. '
      + `${backup.counts.conflict} conflict(s), ${backup.counts.copyMismatch} copy mismatch(es), `
      + `${backup.counts.sourceMissing} unreadable source(s).`;
    return report;
  }

  if (args.backupOnly) {
    report.reason = `Backup complete: ${backup.counts.copied} copied and verified, ${backup.counts.alreadyPreserved} already preserved. Nothing converted (--backup-only).`;
    return report;
  }

  // ---- Phases 2 and 3: masters, then playback from those masters ----------
  const context = { backupRecord: backup.record };
  report.masters = ensureMasters(args, context);
  report.playback = ensurePlayback(args, context, report.masters);

  for (const row of report.masters) {
    if (['convert-failed', 'missing-original', 'refused-no-backup'].includes(row.action)) {
      report.failures.push(`master ${row.id}: ${row.action} — ${row.detail}`);
    }
    if (row.action === 'declared-missing') report.gaps.push(`master ${row.id}: ${row.detail}`);
  }
  // A playback file that cannot be built because its master is a *declared* gap is
  // part of that same gap, not an additional failure.
  const declaredMissing = new Set(report.masters
    .filter((row) => row.action === 'declared-missing')
    .map((row) => row.id));
  for (const row of report.playback) {
    if (row.action === 'skipped-no-master' && declaredMissing.has(row.id)) {
      report.gaps.push(`playback ${row.id}: not built — the master is a declared gap`);
    } else if (['encode-failed', 'refused-no-backup', 'skipped-no-master'].includes(row.action)) {
      report.failures.push(`playback ${row.id}: ${row.action} — ${row.detail}`);
    }
  }

  if (args.dryRun) {
    report.reason = 'Dry run: nothing was written.';
    report.exitCode = report.failures.length ? 1 : 0;
    return report;
  }

  // ---- Machine record of the pass ----------------------------------------
  writeStandardisationRecord({ report, backup, args, startedAt });

  // ---- Manifest ----------------------------------------------------------
  if (args.writeManifest) {
    preservePreviousManifest();
    const manifest = buildStandardisedManifest({ backupRecord: backup.record });
    writeStandardisedManifest(manifest);
    report.manifest = {
      file: 'frontend/public/audio/manifest.json',
      schema: manifest.schema,
      summary: manifest.summary,
      playable: { readyForPlaybackEngine: manifest.playable.readyForPlaybackEngine, integratedWithApplication: false },
    };
  }

  report.exitCode = report.failures.length ? 1 : 0;
  const built = report.masters.filter((row) => row.action === 'converted').length;
  const encoded = report.playback.filter((row) => row.action === 'encoded').length;
  report.reason = report.failures.length
    ? `${report.failures.length} conversion failure(s); ${built} master(s) built, ${encoded} playback file(s) encoded.`
    : `${built} master(s) built, ${encoded} playback file(s) encoded, ${report.gaps.length} declared gap(s).`;
  return report;
}


/** Path shown in reports, relative to the repository, forward slashes. */
function describeRelative(absPath) {
  return path.relative(path.join(AUDIO_ROOT, '..', '..', '..'), absPath).split(path.sep).join('/');
}

/**
 * Write the machine record of this pass: where each master came from, which
 * command produced it, and how its playback file was derived.
 *
 * `validate.mjs` reads this to know that the bytes in the tree are expected to
 * differ from the generation record in `.work/state.json`.
 *
 * @param {{report: object, backup: object, args: object, startedAt: Date}} input
 */
function writeStandardisationRecord(input) {
  const { report, backup, args, startedAt } = input;
  const previousRecord = readStandardisationRecord();
  const assets = {};

  for (const spec of ASSET_SPECS) {
    const masterRow = report.masters.find((row) => row.id === spec.id);
    const playbackRow = report.playback.find((row) => row.id === spec.id);
    const origin = resolveOriginForConversion(spec, backup.record, args.force);
    const originFact = origin ? fileFact(origin.path) : null;
    const originProbe = origin ? probeAudio(origin.path) : null;
    const playbackChecksum = fs.existsSync(playbackPath(spec)) ? fileFact(playbackPath(spec)).sha256 : null;

    // Derivation is a property of the bytes, and it must survive idempotent
    // re-runs. Three durable signals decide it:
    //   - this run encoded it;
    //   - a preserved original exists with exactly these bytes (so the file *is*
    //     the recording, left untouched);
    //   - the path has no preserved original at all, which means it did not exist
    //     before standardisation and therefore was created by this utility.
    const preservedOriginal = backup.record.files?.[spec.playbackFile] || null;
    let playbackDerivation = null;
    if (!playbackChecksum) {
      playbackDerivation = null;
    } else if (playbackRow?.derivation === 'encoded-from-master') {
      playbackDerivation = 'encoded-from-master';
    } else if (preservedOriginal?.sha256 && preservedOriginal.sha256 === playbackChecksum) {
      playbackDerivation = 'original-mp3-preserved';
    } else if (!preservedOriginal) {
      playbackDerivation = 'encoded-from-master';
    } else if (previousRecord?.assets?.[spec.id]?.playbackDerivation === 'encoded-from-master') {
      playbackDerivation = 'encoded-from-master';
    } else {
      playbackDerivation = 'existing-conformant';
    }

    assets[spec.id] = {
      masterFile: spec.masterFile,
      playbackFile: spec.playbackFile,
      origin: origin && originFact?.exists ? {
        file: describeRelative(origin.path),
        role: origin.role,
        sha256: originFact.sha256,
        bytes: originFact.bytes,
        format: originProbe?.formatName ?? null,
        codec: originProbe?.codecName ?? null,
        sampleRate: originProbe?.sampleRate ?? null,
        channels: originProbe?.channels ?? null,
        durationSeconds: originProbe?.durationSeconds ?? null,
        preserved: true,
      } : null,
      master: {
        action: masterRow?.action ?? null,
        checksum: fs.existsSync(masterPath(spec)) ? fileFact(masterPath(spec)).sha256 : null,
        contract: describeMasterFormat(),
      },
      playbackDerivation,
      playback: {
        action: playbackRow?.action ?? null,
        checksum: playbackChecksum,
        contract: describePlaybackFormat(),
      },
      contentStatus: spec.contentExpectation,
    };
  }

  const record = {
    version: 1,
    generatedAt: startedAt.toISOString(),
    tool: {
      utility: 'scripts/que-006-audio/standardise-audio.mjs',
      ffmpeg: report.tooling.ffmpeg,
      ffprobe: report.tooling.ffprobe,
      force: args.force,
    },
    contract: report.contract,
    backup: {
      root: 'frontend/.audio-originals-backup',
      record: 'frontend/.audio-originals-backup/ORIGINALS.json',
      counts: backup.counts,
    },
    note: 'This pass converts containers and sample rates only. It does not alter speech: no '
      + 'normalisation, noise reduction, pitch shift, time stretch, trimming or re-recording.',
    assets,
  };

  const dir = path.dirname(STANDARDISATION_RECORD_PATH);
  fs.mkdirSync(dir, { recursive: true });
  const temp = `${STANDARDISATION_RECORD_PATH}.${process.pid}.tmp`;
  fs.writeFileSync(temp, `${JSON.stringify(record, null, 2)}\n`, 'utf8');
  fs.renameSync(temp, STANDARDISATION_RECORD_PATH);
}

/**
 * Keep the pre-standardisation manifest as evidence.
 *
 * `manifest.json` is a generated artefact and is meant to be rewritten, but the
 * untracked tree keeps no history, so the previous version is copied aside once.
 */
function preservePreviousManifest() {
  const manifestFile = path.join(AUDIO_ROOT, 'manifest.json');
  const archive = path.join(BACKUP_ROOT, 'manifest.pre-standardisation.json');
  if (!fs.existsSync(manifestFile) || fs.existsSync(archive)) return;
  fs.mkdirSync(BACKUP_ROOT, { recursive: true });
  fs.copyFileSync(manifestFile, archive);
}





/** Human-readable report. `quiet` keeps the summary and any gaps only. */
function printReport(report, quiet) {
  const mark = (action) => {
    if (['converted', 'encoded', 'kept-valid'].includes(action)) return 'OK  ';
    if (['would-convert', 'would-encode', 'already-preserved'].includes(action)) return 'PLAN';
    if (action === 'declared-missing') return 'GAP ';
    return 'FAIL';
  };

  console.log('QUE-006 audio standardisation');
  console.log(`  ffmpeg ${report.tooling.ffmpeg || 'missing'} · ffprobe ${report.tooling.ffprobe || 'missing'}`);
  console.log(`  master   ${report.contract.master}`);
  console.log(`  playback ${report.contract.playback}`);
  console.log(`  mode     ${report.dryRun ? 'DRY RUN — nothing written' : 'standardise'}`);

  if (report.backup) {
    const counts = report.backup.counts;
    console.log(`\nBackup — ${report.backup.root}`);
    console.log(`  copied+verified ${counts.copied} · already preserved ${counts.alreadyPreserved}`
      + ` · conflicts ${counts.conflict} · copy mismatches ${counts.copyMismatch}`
      + ` · unreadable ${counts.sourceMissing}`);
    if (!quiet) {
      for (const file of report.backup.files) {
        if (['conflict', 'copy-mismatch', 'source-missing'].includes(file.action)) {
          console.log(`  [FAIL] ${file.rel} — ${file.action}`);
          if (file.note) console.log(`         ${file.note}`);
        }
      }
    }
  }

  if (!quiet && report.masters.length) {
    console.log('\nMasters — frontend/public/audio/**/*.wav');
    for (const row of report.masters) {
      console.log(`  [${mark(row.action)}] ${row.id} — ${row.action}`);
      console.log(`         ${row.detail}`);
    }
    console.log('\nPlayback — frontend/public/audio/**/*.mp3');
    for (const row of report.playback) {
      console.log(`  [${mark(row.action)}] ${row.id} — ${row.action}${row.derivation ? ` (${row.derivation})` : ''}`);
      console.log(`         ${row.detail}`);
    }
  }

  if (report.manifest) {
    const summary = report.manifest.summary;
    console.log('\nManifest — frontend/public/audio/manifest.json');
    console.log(`  schema ${report.manifest.schema}`);
    console.log(`  ${summary.technicalPass}/${summary.total} technically valid · missing ${summary.technicalMissing}`
      + ` · failed ${summary.technicalFail} · content issues ${summary.contentIssues}`
      + ` · human approved ${summary.humanApproved} · pending ${summary.humanPending}`);
    console.log('  prerecorded-audio playback in the frontend: NOT integrated (unchanged by this task)');
  }

  if (report.gaps.length) {
    console.log('\nDeclared gaps (not failures of this pass)');
    for (const gap of report.gaps) console.log(`  - ${gap}`);
  }
  if (report.failures.length) {
    console.log('\nFailures');
    for (const failure of report.failures) console.log(`  - ${failure}`);
  }

  console.log('\nSummary');
  console.log(`  ${report.reason}`);
  console.log(`  exit ${report.exitCode}`);
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
  const report = run(args);
  if (args.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    printReport(report, args.quiet);
  }
  process.exit(report.exitCode);
}
