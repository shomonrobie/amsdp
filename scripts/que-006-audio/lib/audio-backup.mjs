/**
 * QUE-006 — preserve the original recordings before anything converts them.
 *
 * The backup lives at `frontend/.audio-originals-backup/`, outside `public/` so
 * it is never served, and outside the audio directory so no glob over the served
 * tree can pick it up. Original filenames and extensions are kept: a file that is
 * later renamed for the delivery structure is still findable under its old name.
 *
 * Two rules make this trustworthy rather than hopeful:
 *
 *   1. Every copy is re-hashed after it lands. A copy whose SHA-256 does not equal
 *      the source's is reported as a failure, never recorded as preserved.
 *   2. An existing backup file is never overwritten. If the tree's file differs
 *      from the preserved copy, that is a conflict for a human to look at — the
 *      evidence of the original must not be destroyed by a re-run.
 */

import fs from 'node:fs';
import path from 'node:path';

import { BACKUP_RECORD_PATH, BACKUP_ROOT, fileFact, probeAudio, sha256File } from './audio-standard.mjs';

/** Manifest inside the audio directory is a derived artefact, not a recording. */
const DERIVED_FILES = new Set(['manifest.json']);

/** Every file currently in the served audio tree, excluding the manifest. */
export function listAudioTreeFiles(root) {
  const found = [];
  const walk = (dir) => {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const abs = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(abs);
      } else if (entry.isFile()) {
        const rel = path.relative(root, abs).split(path.sep).join('/');
        if (DERIVED_FILES.has(rel)) continue;
        found.push({ rel, abs });
      }
    }
  };
  walk(root);
  return found.sort((a, b) => a.rel.localeCompare(b.rel));
}

/** Read the backup record, tolerating absence. */
export function readBackupRecord(recordPath = BACKUP_RECORD_PATH) {
  try {
    const parsed = JSON.parse(fs.readFileSync(recordPath, 'utf8'));
    if (parsed && typeof parsed === 'object' && parsed.files && typeof parsed.files === 'object') return parsed;
  } catch {
    // No record yet is the normal state before the first standardisation run.
  }
  return { version: 1, createdAt: null, root: null, files: {} };
}

/**
 * Copy every original recording into the backup directory and verify each copy.
 *
 * The record is a snapshot of the tree *before standardisation*, and it stays
 * meaningful across re-runs:
 *
 *   - the first pass preserves every file it finds, whatever the name;
 *   - later passes preserve non-delivery files (`.m4a` sources, notes) but never
 *     a delivery path (`.wav`/`.mp3` the utility itself writes), because those are
 *     our own outputs rather than recordings;
 *   - a delivery path whose preserved copy no longer matches the tree file holds
 *     pre-standardisation bytes and is kept as evidence — `en/phrase/room-suffix.wav`
 *     is exactly that case once its 44.1 kHz master is written over it;
 *   - an entry added after the first snapshot for such a path is pruned, so the
 *     record cannot drift into listing converted files as originals.
 *
 * @param {{audioRoot: string, dryRun?: boolean, now?: Date, deliveryPaths?: Set<string>}} options
 * @returns {{rows: object[], record: object, counts: Record<string, number>}}
 */
export function backupOriginals(options) {
  const { audioRoot, dryRun = false, deliveryPaths = new Set() } = options;
  const now = options.now || new Date();
  const record = readBackupRecord();
  record.version = 1;
  record.root = 'frontend/.audio-originals-backup';
  const firstCapture = !record.createdAt;
  if (firstCapture) record.createdAt = now.toISOString();
  record.updatedAt = now.toISOString();

  const rows = [];
  const counts = {
    copied: 0, alreadyPreserved: 0, conflict: 0, copyMismatch: 0, sourceMissing: 0,
    skippedDerived: 0, prunedDerived: 0, keptSuperseded: 0,
  };

  const superseded = new Set();
  for (const rel of Object.keys(record.files || {})) {
    if (!deliveryPaths.has(rel)) continue;
    const preserved = record.files[rel];
    const current = fileFact(path.join(audioRoot, ...rel.split('/')));
    if (!current.exists || (preserved.sha256 && current.sha256 && preserved.sha256 !== current.sha256)) {
      superseded.add(rel);
      counts.keptSuperseded += 1;
      continue;
    }
    const capturedLater = preserved.preservedAt && preserved.preservedAt !== record.createdAt;
    if (!capturedLater) continue;
    if (!dryRun) {
      try {
        fs.unlinkSync(path.join(BACKUP_ROOT, ...rel.split('/')));
      } catch {
        // Already absent; the record entry still needs to go.
      }
      delete record.files[rel];
    }
    counts.prunedDerived += 1;
  }

  for (const file of listAudioTreeFiles(audioRoot)) {
    const captured = Boolean(record.files?.[file.rel]);
    if (deliveryPaths.has(file.rel) && !superseded.has(file.rel) && !firstCapture && !captured) {
      counts.skippedDerived += 1;
      continue;
    }
    const target = path.join(BACKUP_ROOT, ...file.rel.split('/'));
    const source = fileFact(file.abs);
    const existing = fileFact(target);
    const probe = probeAudio(file.abs);

    /** @type {object} */
    const row = {
      rel: file.rel,
      backupFile: file.rel,
      bytes: source.bytes,
      sha256: source.sha256,
      modifiedAt: source.modifiedAt,
      format: probe.formatName,
      codec: probe.codecName,
      sampleRate: probe.sampleRate,
      channels: probe.channels,
      bitsPerSample: probe.bitsPerSample,
      durationSeconds: probe.durationSeconds,
    };

    if (!source.exists) {
      row.action = 'source-missing';
      counts.sourceMissing += 1;
      rows.push(row);
      continue;
    }

    if (superseded.has(file.rel)) {
      const preserved = record.files[file.rel];
      rows.push({
        ...row,
        bytes: preserved?.bytes ?? existing.bytes,
        sha256: preserved?.sha256 ?? existing.sha256,
        backupSha256: existing.sha256,
        action: 'original-preserved-superseded',
        note: 'The tree file has since been replaced by a standardised master. The preserved copy holds '
          + 'the pre-standardisation bytes recorded in ORIGINALS.json.',
      });
      continue;
    }

    if (existing.exists) {
      if (existing.sha256 === source.sha256) {
        row.action = 'already-preserved';
        row.backupSha256 = existing.sha256;
        counts.alreadyPreserved += 1;
      } else {
        row.action = 'conflict';
        row.backupSha256 = existing.sha256;
        row.note = 'The backup copy differs from the file in the audio tree. The preserved original was '
          + 'kept and this file was NOT overwritten; a human must decide which is authoritative.';
        counts.conflict += 1;
      }
      rows.push(row);
      continue;
    }

    if (dryRun) {
      row.action = 'would-copy';
      rows.push(row);
      continue;
    }

    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(file.abs, target);
    const after = sha256File(target);
    row.backupSha256 = after;
    if (after === source.sha256) {
      row.action = 'copied-verified';
      counts.copied += 1;
    } else {
      row.action = 'copy-mismatch';
      row.note = 'The copy does not hash to the source. Treat the backup as unreliable for this file.';
      counts.copyMismatch += 1;
    }
    rows.push(row);
  }

  record.files = {
    ...record.files,
    ...Object.fromEntries(rows
      .filter((row) => row.sha256)
      .map((row) => [row.rel, {
        bytes: row.bytes,
        sha256: row.sha256,
        backupSha256: row.backupSha256 || null,
        backupRelativePath: `frontend/.audio-originals-backup/${row.rel}`,
        preservedAt: record.files?.[row.rel]?.preservedAt || now.toISOString(),
        lastSeenAt: now.toISOString(),
        format: row.format,
        codec: row.codec,
        sampleRate: row.sampleRate,
        channels: row.channels,
        bitsPerSample: row.bitsPerSample,
        durationSeconds: row.durationSeconds,
        status: row.action,
      }])),
  };
  record.counts = counts;

  if (!dryRun) {
    fs.mkdirSync(BACKUP_ROOT, { recursive: true });
    const temp = `${BACKUP_RECORD_PATH}.${process.pid}.tmp`;
    fs.writeFileSync(temp, `${JSON.stringify(record, null, 2)}\n`, 'utf8');
    fs.renameSync(temp, BACKUP_RECORD_PATH);
  }

  return { rows, record, counts };
}

