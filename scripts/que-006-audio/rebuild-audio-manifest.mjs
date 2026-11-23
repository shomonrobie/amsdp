#!/usr/bin/env node
/**
 * QUE-006 — rebuild `frontend/public/audio/manifest.json` from the files on disk.
 *
 *   node scripts/que-006-audio/rebuild-audio-manifest.mjs
 *   node scripts/que-006-audio/rebuild-audio-manifest.mjs --check   # report drift, write nothing
 *
 * Useful after a manual repair (for example restoring a file from
 * `frontend/.audio-originals-backup/`): the manifest is regenerated from real
 * bytes and real hashes rather than edited by hand.
 *
 * Approvals are not invented here. `humanReviewStatus` carries forward only when a
 * previous manifest recorded a human decision on byte-identical playback audio;
 * otherwise it stays `pending`.
 *
 * Exit codes: 0 manifest written (or already current) | 1 --check found drift |
 *             2 usage error.
 */

import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

import { MANIFEST_PATH } from './lib/paths.mjs';
import { buildStandardisedManifest, writeStandardisedManifest } from './lib/audio-standard-manifest.mjs';

const USAGE = `
QUE-006 audio manifest rebuild

Usage:
  node scripts/que-006-audio/rebuild-audio-manifest.mjs [options]

Options:
  --check      compare with the manifest on disk; write nothing
  --quiet      print the summary only
  --help, -h   show this help

Exit codes: 0 written or already current | 1 --check found drift | 2 usage error.
`;

/** @param {string[]} argv */
export function parseArgs(argv) {
  const args = { check: false, quiet: false, help: false };
  for (const arg of argv) {
    switch (arg) {
      case '--check': args.check = true; break;
      case '--quiet': args.quiet = true; break;
      case '--help': case '-h': args.help = true; break;
      default: throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}

/** Fields that describe the manifest itself, not the audio, and so may differ. */
const VOLATILE = new Set(['generatedAt']);

/** Structural comparison that ignores the generation timestamp. */
function driftAgainstDisk(manifest) {
  if (!fs.existsSync(MANIFEST_PATH)) return ['manifest.json does not exist'];
  let existing;
  try {
    existing = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
  } catch (err) {
    return [`manifest.json does not parse: ${err.message}`];
  }
  const strip = (value) => JSON.stringify(value, (key, inner) => (VOLATILE.has(key) ? undefined : inner));
  if (strip(existing) === strip(manifest)) return [];

  const drift = [];
  const current = new Map((existing.assets || []).map((entry) => [entry.id, entry]));
  for (const entry of manifest.assets) {
    const prior = current.get(entry.id);
    if (!prior) { drift.push(`${entry.id}: absent from the manifest on disk`); continue; }
    for (const field of ['masterChecksum', 'playbackChecksum', 'technicalValidationStatus', 'humanReviewStatus', 'spokenText']) {
      if (prior[field] !== entry[field]) drift.push(`${entry.id}.${field}: ${JSON.stringify(prior[field])} -> ${JSON.stringify(entry[field])}`);
    }
  }
  for (const summaryKey of Object.keys(manifest.summary)) {
    if (existing.summary?.[summaryKey] !== manifest.summary[summaryKey]) {
      drift.push(`summary.${summaryKey}: ${JSON.stringify(existing.summary?.[summaryKey])} -> ${JSON.stringify(manifest.summary[summaryKey])}`);
    }
  }
  return drift.length ? drift : ['manifest differs outside the compared asset and summary fields'];
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
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

  const manifest = buildStandardisedManifest();
  if (args.check) {
    const drift = driftAgainstDisk(manifest);
    if (drift.length === 0) {
      if (!args.quiet) console.log('manifest.json is current — matches the files on disk');
      process.exit(0);
    }
    console.log('manifest.json is stale:');
    for (const line of drift) console.log(`  - ${line}`);
    process.exit(1);
  }

  writeStandardisedManifest(manifest);
  const { summary } = manifest;
  console.log('manifest.json rebuilt from the files on disk');
  console.log(`  ${summary.technicalPass}/${summary.total} technically valid · missing ${summary.technicalMissing}`
    + ` · failed ${summary.technicalFail} · content issues ${summary.contentIssues}`);
  console.log(`  human approved ${summary.humanApproved} · review pending ${summary.humanPending}`);
  console.log('  prerecorded-audio playback in the frontend: not integrated');
}
