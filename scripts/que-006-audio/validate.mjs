#!/usr/bin/env node
/**
 * QUE-006 — validate the generated audio set, independently of the generator.
 *
 *   node scripts/que-006-audio/validate.mjs
 *   node scripts/que-006-audio/validate.mjs --allow-missing
 *   node scripts/que-006-audio/validate.mjs --json
 *
 * What this proves, and what it does not:
 *
 *   PROVES   each expected file exists, is non-empty, its container parses (RIFF
 *            chunk walk for WAV, frame-header walk for MP3), its declared sample
 *            rate/channels/bit depth are sane, its duration sits inside the band
 *            expected for its category, it is not digitally silent (except the
 *            punctuation pause), its SHA-256 matches what the generator recorded,
 *            no two clips are byte-identical, and manifest.json agrees with both
 *            the catalogue and the files on disk.
 *   DOES NOT PROVE that a clip contains the right words, that the Bangla is
 *            pronounced correctly, or that the level suits a clinic. Those need a
 *            human listener. Decode depth is reported honestly per run: when
 *            ffprobe/ffmpeg are installed (see lib/decode.mjs) every clip is
 *            actually decoded and the decoded facts are cross-checked against the
 *            container; when they are not, "decodable" means only "the container
 *            is structurally valid". Either way each row carries the method used
 *            in `decodeVerifiedBy`, so a structural parse is never reported as a
 *            decode.
 *
 * Exit codes: 0 all checks pass | 1 check failure(s) | 2 usage error.
 */

import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import {
  ASSETS,
  CATALOGUE_ASSET_COUNT,
  PUNCTUATION_PAUSE_MS,
  SPOKEN_TEXT_OVERRIDES,
  recordedTextFor,
  diffAgainstDoc,
  diffComposedAgainstApproved,
} from './catalogue.mjs';
import { MANIFEST_PATH, STATE_PATH, REPO_ROOT, audioPathFor } from './lib/paths.mjs';
import { inspectAudioFile } from './lib/audio-file.mjs';
import { detectDecoder, verifyDecode } from './lib/decode.mjs';
import { buildManifest, readState } from './lib/manifest.mjs';
import { readStandardisationRecord } from './lib/audio-standard-manifest.mjs';
import { loadApprovedTemplates } from './lib/approved-templates.mjs';

const EXPECTED_SAMPLE_RATE = 24000;

/**
 * Detect a tree that has been through the format-standardisation pass.
 *
 * The generation stage wrote 24 kHz WAVs and recorded their checksums in
 * `.work/state.json`. After standardisation the masters are 44.1 kHz and their
 * bytes legitimately differ, so the generation expectations no longer describe
 * the files. When `.work/standardisation.json` exists this module switches its
 * expected sample rate, checksum source and manifest field names to that record
 * and says so in the report — it never silently loosens a check.
 */
function loadStandardisationContext(manifest) {
  const record = readStandardisationRecord();
  const assets = record?.assets || {};
  if (Object.keys(assets).length === 0) return null;
  return {
    record,
    assets,
    sampleRate: manifest?.formats?.master?.sampleRate ?? 44100,
    standardisedManifest: Boolean(manifest?.schema && String(manifest.schema).includes('/2.')),
  };
}
const DURATION_BAND_MS = {
  number: { min: 120, max: 3500 },
  phrase: { min: 150, max: 9000 },
};
const PAUSE_TOLERANCE_MS = 20;
// A decoder reports duration from the frame count; the container computes it
// from byte size / byte rate. They agree to the nearest sample frame, so any
// larger gap means the two disagree about the file itself.
const DECODE_DURATION_TOLERANCE_MS = 50;

const USAGE = `
QUE-006 audio validation

Usage:
  node scripts/que-006-audio/validate.mjs [--allow-missing] [--json] [--quiet]

Options:
  --allow-missing   treat absent files as pending work (warning) instead of failures
  --json            print the report as JSON (no prose)
  --quiet           print failures and the verdict only

Exit codes: 0 all checks pass | 1 check failure(s) | 2 usage error.
`;

/** @param {string[]} argv */
export function parseArgs(argv) {
  const args = { allowMissing: false, json: false, quiet: false, help: false };
  for (const arg of argv) {
    switch (arg) {
      case '--allow-missing': args.allowMissing = true; break;
      case '--json': args.json = true; break;
      case '--quiet': args.quiet = true; break;
      case '--help': case '-h': args.help = true; break;
      default: throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}
/** @typedef {{name: string, level: 'pass'|'warn'|'fail', detail: string}} Check */

const percent = (value, total) => (total ? `${((value / total) * 100).toFixed(0)}%` : 'n/a');

/**
 * Group A — the catalogue itself must be internally consistent before any file
 * verdict means anything. A wrong catalogue silently invalidates every clip.
 *
 * @returns {{checks: Check[], failures: string[]}}
 */
function checkCatalogueIntegrity() {
  const checks = [];
  const failures = [];

  const doc = diffAgainstDoc(REPO_ROOT);
  if (doc.ok) {
    checks.push({ name: 'catalogue code vs document', level: 'pass', detail: `${doc.documentRows} rows agree with catalogue.mjs` });
  } else {
    checks.push({ name: 'catalogue code vs document', level: 'fail', detail: doc.mismatches.join('; ') || 'mismatch' });
    failures.push(...doc.mismatches.map((m) => `catalogue/${m}`));
  }

  let approved;
  try {
    approved = loadApprovedTemplates();
    const composed = diffComposedAgainstApproved(approved);
    if (composed.length === 0) {
      checks.push({ name: 'composed clips vs approved templates', level: 'pass', detail: 'en and bn, with-room and no-room compose identically to the approved wording' });
    } else {
      checks.push({ name: 'composed clips vs approved templates', level: 'fail', detail: composed.join('; ') });
      failures.push(...composed.map((m) => `composed/${m}`));
    }
  } catch (err) {
    checks.push({ name: 'composed clips vs approved templates', level: 'fail', detail: `could not read approved templates: ${err.message}` });
    failures.push('composed/approved templates unreadable');
  }

  const en = ASSETS.filter((a) => a.language === 'en').length;
  const bn = ASSETS.filter((a) => a.language === 'bn').length;
  const countOk = ASSETS.length === CATALOGUE_ASSET_COUNT && CATALOGUE_ASSET_COUNT === 28 && en === 14 && bn === 14;
  checks.push({
    name: 'catalogue composition',
    level: countOk ? 'pass' : 'fail',
    detail: `${ASSETS.length} assets (en ${en}, bn ${bn}), expected 28 (en 14, bn 14)`,
  });
  if (!countOk) failures.push('catalogue/composition');

  // Declared deviations are informational, never silently applied.
  for (const [id, override] of Object.entries(SPOKEN_TEXT_OVERRIDES)) {
    checks.push({
      name: `declared override ${id}`,
      level: 'warn',
      detail: `recorded ${JSON.stringify(recordedTextFor({ id, spokenText: '' }))} instead of the catalogue cell — ${override.reason}`,
    });
  }

  return { checks, failures };
}


/**
 * Group B — one record per catalogue asset, judged from the bytes on disk.
 * The manifest is *compared against* the disk here, never used as the source of
 * truth, so a stale or hand-edited manifest cannot certify a bad file.
 *
 * @param {Record<string, any>} state
 * @param {Record<string, any>} manifestAssetsById
 * @param {boolean} allowMissing
 */
function checkAssets(state, manifestAssetsById, allowMissing, context) {
  const rows = [];
  const failures = [];
  const warnings = [];
  const decoder = detectDecoder();

  for (const asset of ASSETS) {
    const record = inspectAudioFile(audioPathFor(asset), { expectSilence: asset.synthetic === 'silence' });
    const manifestEntry = manifestAssetsById[asset.id] || null;
    const recorded = state.assets?.[asset.id] || null;
    const expectSilence = asset.synthetic === 'silence';
    // Standardised trees: 44.1 kHz masters, checksums from the standardisation
    // record, and the v2 manifest field names.
    const expectedRate = context ? context.sampleRate : EXPECTED_SAMPLE_RATE;
    const standardisedEntry = context ? (context.assets?.[asset.id] || null) : null;
    const problems = [];
    let decodeRow = null;

    if (!record.exists) {
      problems.push('file not present');
    } else if (record.size === 0) {
      problems.push('zero bytes');
    } else {
      if (!record.decodable) problems.push(`container does not parse (${record.problems.join('; ') || 'unknown'})`);
      if (record.format !== 'wav') problems.push(`container is ${record.format}, expected wav`);
      if (record.sampleRate !== expectedRate) problems.push(`sample rate ${record.sampleRate}, expected ${expectedRate}`);
      if (record.channels !== 1) problems.push(`${record.channels} channel(s), expected mono`);
      if (record.bitsPerSample !== 16) problems.push(`${record.bitsPerSample}-bit samples, expected 16-bit`);

      const durationMs = record.durationMs;
      if (!durationMs) {
        problems.push('duration is zero or unknown');
      } else if (expectSilence) {
        if (Math.abs(durationMs - PUNCTUATION_PAUSE_MS) > PAUSE_TOLERANCE_MS) {
          problems.push(`pause is ${durationMs} ms, expected ${PUNCTUATION_PAUSE_MS} ±${PAUSE_TOLERANCE_MS} ms`);
        }
        if (!record.silent) problems.push('pause asset is not silent — the engine must not speak this cell');
      } else {
        const band = DURATION_BAND_MS[asset.category] || DURATION_BAND_MS.phrase;
        if (durationMs < band.min || durationMs > band.max) {
          problems.push(`duration ${durationMs} ms is outside the ${asset.category} band ${band.min}–${band.max} ms`);
        }
        if (record.silent) problems.push('audio is digitally silent — nothing was spoken');
      }

      if (context) {
        // Authority after standardisation is the standardisation record, not the
        // generation record: the bytes were deliberately re-derived.
        const expectedSha = standardisedEntry?.master?.checksum || null;
        if (!standardisedEntry) {
          problems.push('absent from .work/standardisation.json (not produced by the standardisation pass)');
        } else if (expectedSha && record.sha256 !== expectedSha) {
          problems.push('sha256 differs from the standardisation record (master replaced after conversion)');
        }
      } else if (!recorded) {
        problems.push('no generation record in .work/state.json (unrecorded file)');
      } else if (recorded.sha256 && record.sha256 !== recorded.sha256) {
        problems.push('sha256 differs from the generation record (file replaced after generation)');
      }

      if (!manifestEntry) {
        problems.push('absent from manifest.json');
      } else if (context) {
        if (manifestEntry.masterChecksum !== record.sha256) problems.push('manifest masterChecksum does not match the file on disk');
        if (manifestEntry.masterBytes !== record.size) problems.push('manifest masterBytes does not match the file on disk');
        if (manifestEntry.technicalValidationStatus !== 'pass') {
          problems.push(`manifest records technicalValidationStatus "${manifestEntry.technicalValidationStatus}"`);
        }
      } else {
        if (manifestEntry.sha256 !== record.sha256) problems.push('manifest sha256 does not match the file on disk');
        if (manifestEntry.fileSizeBytes !== record.size) problems.push('manifest size does not match the file on disk');
        if (manifestEntry.validationStatus !== 'ready') problems.push(`manifest records status "${manifestEntry.validationStatus}"`);
      }

      // Optional: a real decoder is stronger evidence than a container parse.
      // Run only when ffprobe/ffmpeg exist, and record the method per row so a
      // structure-only run can never be mistaken for a decode.
      if (decoder.available) {
        decodeRow = verifyDecode(audioPathFor(asset));
        const probe = decodeRow.probe || {};
        if (!decodeRow.verified) {
          problems.push(`decoder check failed: ${decodeRow.detail}`);
        } else {
          if (probe.sampleRate !== null && probe.sampleRate !== undefined && probe.sampleRate !== record.sampleRate) {
            problems.push(`decoder reports ${probe.sampleRate} Hz, container declares ${record.sampleRate} Hz`);
          }
          if (probe.channels !== null && probe.channels !== undefined && probe.channels !== record.channels) {
            problems.push(`decoder reports ${probe.channels} channel(s), container declares ${record.channels}`);
          }
          if (probe.bitsPerSample !== null && probe.bitsPerSample !== undefined
            && record.bitsPerSample !== null && probe.bitsPerSample !== record.bitsPerSample) {
            problems.push(`decoder reports ${probe.bitsPerSample}-bit, container declares ${record.bitsPerSample}-bit`);
          }
          if (probe.durationMs !== null && probe.durationMs !== undefined
            && record.durationMs !== null
            && Math.abs(probe.durationMs - record.durationMs) > DECODE_DURATION_TOLERANCE_MS) {
            problems.push(`decoder measures ${probe.durationMs} ms, container declares ${record.durationMs} ms`);
          }
        }
      }
    }

    const status = problems.length === 0 ? 'pass' : (!record.exists && allowMissing ? 'warn' : 'fail');
    if (status === 'fail') failures.push(asset.id);
    if (status === 'warn') warnings.push(asset.id);
    rows.push({
      id: asset.id,
      filename: asset.filename,
      status,
      problems,
      exists: record.exists,
      fileSizeBytes: record.size,
      format: record.format,
      sampleRate: record.sampleRate,
      channels: record.channels,
      bitsPerSample: record.bitsPerSample,
      durationMs: record.durationMs,
      peakAmplitude: record.peakAmplitude,
      silent: record.silent,
      sha256: record.sha256,
      // Stated per row so no reader can mistake a structural parse for a decode.
      decodeVerifiedBy: decodeRow && decodeRow.verified ? decodeRow.method : record.decodeVerifiedBy,
      decodeDetail: decodeRow ? decodeRow.detail : null,
      decoderDurationMs: decodeRow && decodeRow.probe ? decodeRow.probe.durationMs : null,
      decoderCodec: decodeRow && decodeRow.probe ? decodeRow.probe.codecName : null,
      synthetic: asset.synthetic || null,
    });
  }

  return { rows, failures, warnings };
}



/**
 * Group C — cross-file properties no single file can prove: identical bytes for
 * different sentences (a real API failure mode) and manifest/disk agreement.
 *
 * @param {ReturnType<typeof checkAssets>['rows']} rows
 * @param {Record<string, any>} manifest
 * @param {Record<string, any>} state
 */
function checkConsistency(rows, manifest, state, context) {
  const checks = [];
  const failures = [];

  const byHash = new Map();
  for (const row of rows) {
    if (!row.sha256 || row.synthetic === 'silence') continue;
    if (!byHash.has(row.sha256)) byHash.set(row.sha256, []);
    byHash.get(row.sha256).push(row.id);
  }
  const duplicates = [...byHash.values()].filter((ids) => ids.length > 1);
  if (duplicates.length === 0) {
    checks.push({ name: 'distinct audio per clip', level: 'pass', detail: `${byHash.size} spoken clips, all byte-distinct` });
  } else {
    checks.push({
      name: 'distinct audio per clip',
      level: 'fail',
      detail: `identical bytes for different texts: ${duplicates.map((ids) => ids.join(' = ')).join('; ')}`,
    });
    failures.push('consistency/duplicate-audio');
  }

  if (context) {
    // Standardised tree: the manifest and the standardisation record are compared
    // against the bytes on disk. Recomputing the generation manifest here would be
    // meaningless — the files were deliberately re-derived at 44.1 kHz.
    const byId = new Map(rows.map((row) => [row.id, row]));
    const drifted = [];
    for (const asset of ASSETS) {
      const entry = (manifest.assets || []).find((candidate) => candidate.id === asset.id);
      const standardised = context.assets?.[asset.id] || null;
      const diskSha = byId.get(asset.id)?.sha256 || null;
      if (!entry) {
        drifted.push(`${asset.id}: absent from manifest.json`);
        continue;
      }
      if ((entry.masterChecksum || null) !== diskSha) drifted.push(`${asset.id}: manifest masterChecksum differs from the file on disk`);
      if ((standardised?.master?.checksum || null) !== diskSha) drifted.push(`${asset.id}: .work/standardisation.json checksum differs from the file on disk`);
    }
    if (drifted.length === 0) {
      checks.push({
        name: 'manifest and standardisation record vs disk',
        level: 'pass',
        detail: `${rows.length} clips: manifest masterChecksum and .work/standardisation.json checksums both match the bytes on disk`,
      });
    } else {
      checks.push({ name: 'manifest and standardisation record vs disk', level: 'fail', detail: drifted.join('; ') });
      failures.push('consistency/stale-standardised-manifest');
    }
  } else {
    const recomputed = buildManifest({ state, generator: manifest.generator });
    const fields = ['total', 'ready', 'missing', 'invalid', 'modifiedSinceGeneration', 'unrecorded', 'catalogueComplete'];
    const drift = fields.filter((field) => recomputed.summary[field] !== manifest.summary?.[field]);
    if (drift.length === 0) {
      checks.push({
        name: 'manifest summary vs disk',
        level: 'pass',
        detail: `${manifest.summary.ready}/${manifest.summary.total} ready — matches a fresh recomputation`,
      });
    } else {
      checks.push({
        name: 'manifest summary vs disk',
        level: 'fail',
        detail: `stale manifest — ${drift.map((field) => `${field}: ${manifest.summary?.[field]} in file vs ${recomputed.summary[field]} on disk`).join('; ')}`,
      });
      failures.push('consistency/stale-manifest');
    }

    const statusDrift = ASSETS.filter((asset) => {
      const entry = (manifest.assets || []).find((candidate) => candidate.id === asset.id);
      const fresh = recomputed.assets.find((candidate) => candidate.id === asset.id);
      return !entry || entry.validationStatus !== fresh.validationStatus;
    }).map((asset) => asset.id);
    if (statusDrift.length === 0) {
      checks.push({ name: 'manifest per-asset status', level: 'pass', detail: 'every status matches the file on disk' });
    } else {
      checks.push({ name: 'manifest per-asset status', level: 'fail', detail: `stale status for ${statusDrift.join(', ')}` });
      failures.push('consistency/stale-status');
    }
  }

  const honestClaims = (manifest.playable || {}).integratedWithApplication === false;
  checks.push({
    name: 'manifest claims no integration',
    level: honestClaims ? 'pass' : 'fail',
    detail: honestClaims
      ? 'integratedWithApplication=false — the frontend does not consume this manifest yet'
      : 'integratedWithApplication is not false — the manifest would overclaim playback',
  });
  if (!honestClaims) failures.push('consistency/overclaim');

  return { checks, failures };
}


/**
 * Runner: read what exists, run the three check groups, print, exit.
 *
 * @param {{allowMissing: boolean, json: boolean, quiet: boolean}} args
 */
export async function runValidation(args) {
  const decoder = detectDecoder();
  if (!fs.existsSync(MANIFEST_PATH)) {
    return {
      verdict: 'fail',
      exitCode: 1,
      reason: `manifest.json is absent (${MANIFEST_PATH}). Run generate.mjs --rebuild-manifest first; without it a file set cannot be certified.`,
      counts: { total: ASSETS.length, pass: 0, warn: 0, fail: ASSETS.length, coverage: '0%' },
      checks: [],
      assets: [],
      failures: ['manifest/absent'],
      warnings: [],
      limits: {
        decoder: decoder.available ? decoder.detail : 'none',
        method: 'none',
        verified: 'nothing',
        notVerified: 'everything — no manifest to validate against',
      },
    };
  }

  const state = readState(STATE_PATH);
  const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
  const manifestAssetsById = Object.fromEntries((manifest.assets || []).map((entry) => [entry.id, entry]));
  const context = loadStandardisationContext(manifest);

  const catalogue = checkCatalogueIntegrity();
  const assets = checkAssets(state, manifestAssetsById, args.allowMissing, context);
  const consistency = checkConsistency(assets.rows, manifest, state, context);

  const checks = [...catalogue.checks, ...consistency.checks];
  if (context) {
    checks.push({
      name: 'standardisation stage detected',
      level: 'pass',
      detail: `masters are ${context.sampleRate} Hz; checksums come from .work/standardisation.json and the `
        + `${context.standardisedManifest ? 'v2' : 'unexpected'} manifest schema is in use. Generation-stage `
        + 'expectations (24 kHz, .work/state.json checksums) are replaced, not relaxed.',
    });
  }
  const failures = [...catalogue.failures, ...assets.failures, ...consistency.failures];
  const warnings = [...assets.warnings];
  const passCount = assets.rows.filter((row) => row.status === 'pass').length;
  const verdict = failures.length === 0 ? 'pass' : 'fail';
  let reason;
  if (verdict === 'fail') {
    reason = `${failures.length} failure(s) across ${ASSETS.length} catalogue clips`;
  } else if (warnings.length === 0) {
    reason = `all ${ASSETS.length} catalogue clips pass structural validation`;
  } else {
    reason = `no failures; ${passCount}/${ASSETS.length} clips validated on disk, ${warnings.length} still pending generation (--allow-missing was set)`;
  }

  return {
    verdict,
    exitCode: verdict === 'pass' ? 0 : 1,
    reason,
    counts: {
      total: ASSETS.length,
      pass: passCount,
      warn: warnings.length,
      fail: failures.length,
      coverage: percent(passCount, ASSETS.length),
    },
    checks,
    assets: assets.rows,
    failures,
    warnings,
    limits: {
      decoder: decoder.available ? decoder.detail : 'none on this machine — no ffmpeg or ffprobe available',
      method: decoder.available
        ? 'riff/mpeg container parse + ffprobe stream facts + ffmpeg full-file decode'
        : 'container-structure only — a structural parse is not a decode',
      verified: decoder.available
        ? 'existence, size, container parse, declared sample rate/channels/bit depth, duration band, digital silence, sha256 vs generation record, manifest agreement, byte-distinctness, and codec-level decode of every sample (ffprobe + ffmpeg, cross-checked against the container)'
        : 'existence, size, RIFF/MPEG container parse, declared sample rate/channels/bit depth, duration band, digital silence, sha256 vs generation record, manifest agreement, byte-distinctness',
      notVerified: decoder.available
        ? 'that the words are correct, Bangla pronunciation, perceived loudness, and whether the voice suits a clinic'
        : 'that the words are correct, Bangla pronunciation, perceived loudness, and codec-level decode of the samples',
    },
  };
}

/**
 * Print a report for humans. `quiet` keeps only problems and the verdict.
 *
 * @param {Awaited<ReturnType<typeof runValidation>>} report
 * @param {boolean} quiet
 */
function printReport(report, quiet) {
  const tag = (level) => (level === 'pass' ? 'PASS' : level === 'warn' ? 'WARN' : 'FAIL');
  const isConsistency = (name) => name.includes('manifest') || name.includes('distinct audio');

  if (!quiet) {
    console.log('QUE-006 audio validation');
    console.log(`  catalogue ${ASSETS.length} assets · manifest frontend/public/audio/manifest.json`);
    console.log(`  decoder   ${report.limits.decoder}`);
    console.log(`  method    ${report.limits.method}`);
    console.log('\nCatalogue integrity');
    for (const check of report.checks.filter((candidate) => !isConsistency(candidate.name))) {
      console.log(`  [${tag(check.level)}] ${check.name}`);
      console.log(`         ${check.detail}`);
    }
    console.log('\nManifest and cross-file consistency');
    for (const check of report.checks.filter((candidate) => isConsistency(candidate.name))) {
      console.log(`  [${tag(check.level)}] ${check.name}`);
      console.log(`         ${check.detail}`);
    }
    console.log('\nPer-asset results');
    for (const row of report.assets) {
      const duration = row.durationMs === null ? 'n/a' : `${row.durationMs} ms`;
      const mark = row.status === 'pass' ? 'OK  ' : row.status === 'warn' ? 'WAIT' : 'FAIL';
      console.log(`  [${mark}] ${row.id} — ${duration}, ${row.fileSizeBytes} B, parsed by ${row.decodeVerifiedBy}`);
    }
  }

  const problems = report.assets.filter((row) => row.status !== 'pass');
  if (problems.length) {
    console.log('\nProblems');
    for (const row of problems) {
      console.log(`  ${row.id}`);
      for (const problem of row.problems) console.log(`    - ${problem}`);
    }
  }

  console.log('\nSummary');
  console.log(`  pass ${report.counts.pass}/${report.counts.total} (${report.counts.coverage}) · warn ${report.counts.warn} · fail ${report.counts.fail}`);
  console.log(`  verdict ${report.verdict.toUpperCase()} — ${report.reason}`);
  if (!quiet) {
    console.log('\nWhat this does not establish');
    console.log(`  ${report.limits.notVerified}.`);
    console.log('  Every clip still needs human listening review, and Bangla in particular a fluent speaker.');
  }
}

export async function main(argv = process.argv.slice(2)) {
  let args;
  try {
    args = parseArgs(argv);
  } catch (err) {
    console.error(`ERROR ${err.message}\n${USAGE}`);
    return 2;
  }
  if (args.help) {
    console.log(USAGE.trim());
    return 0;
  }

  const report = await runValidation(args);
  if (args.json) console.log(JSON.stringify(report, null, 2));
  else printReport(report, args.quiet);
  return report.exitCode;
}

const invokedDirectly = process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;

if (invokedDirectly) {
  main()
    .then((code) => process.exit(code))
    .catch((err) => {
      console.error(`FATAL ${err && err.message ? err.message : err}`);
      process.exit(1);
    });
}

