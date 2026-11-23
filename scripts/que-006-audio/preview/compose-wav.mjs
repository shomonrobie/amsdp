#!/usr/bin/env node
/**
 * QUE-006 — build the fixed 20-sample composed-announcement collection.
 *
 * This is a **verification preparation** tool, not an audio-processing step, and
 * its guarantees are structural rather than promises:
 *
 *   - The WAV masters are read only. Every file under `frontend/public/audio/`
 *     (including `manifest.json`) is hashed before and after the run, and the run
 *     fails if any byte moved.
 *   - Concatenation is byte-level. `lib/audio-file.mjs#parseWav` locates each
 *     source's PCM `data` chunk and those bytes are copied verbatim into the
 *     output, so a re-encode, a resample, a gain change, a trim or a fade is
 *     impossible by construction — there is no code path that touches a sample.
 *     Every copied range is then re-hashed inside the written file and compared
 *     against the source chunk, so the claim is checked, not asserted.
 *   - The default junction pause is 0 ms (`compose.mjs`), because the catalogue
 *     specifies direct concatenation and the shipped clips already carry their
 *     own trailing room tone. No pause is inserted between a room number and its
 *     bound locative suffix / full stop.
 *   - `manifest.json` is never written, and no `humanReviewStatus` is touched.
 *
 * The expected wording is never hard-coded here: it is rendered from the
 * approved templates via `lib/approved-templates.mjs` (which reads
 * `frontend/lib/announcements/content.js` as text), and then every rendered
 * string is compared against what `buildAnnouncement()` itself returns in a
 * child process. If the two ever disagree this script exits non-zero instead of
 * producing samples whose captions differ from the product's wording.
 *
 * Usage:
 *   node scripts/que-006-audio/preview/compose-wav.mjs [--quiet] [--force]
 *
 *   --quiet  print only the closing summary
 *   --force  rebuild samples that already exist (default: reuse valid ones)
 */

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { AUDIO_ROOT, MANIFEST_PATH, REPO_ROOT } from '../lib/paths.mjs';
import { loadApprovedTemplates } from '../lib/approved-templates.mjs';
import { parseWav } from '../lib/audio-file.mjs';
import { detectDecoder, verifyDecode } from '../lib/decode.mjs';
import {
  DEFAULT_PAUSE_MS,
  MAX_DIGITS,
  PAUSE_OPTIONS_MS,
  digitAssetId,
  pauseBefore,
  planSegments,
} from './compose.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
/** Generated artefacts live beside the tool and are git-ignored (see .gitignore). */
const GENERATED_DIR = path.join(here, 'generated');
const SAMPLES_DIR = path.join(GENERATED_DIR, 'samples');
const CONTENT_MODULE = path.join(REPO_ROOT, 'frontend', 'lib', 'announcements', 'content.js');

/** The delivery contract every master must already satisfy. */
const CONTRACT = Object.freeze({ format: 1, channels: 1, sampleRate: 44100, bitsPerSample: 16 });

/** The fixed test matrix from the task (token, room). */
const CASES = Object.freeze([
  { test: 'basic', token: '4', room: '305' },
  { test: 'multiple-digits', token: '12', room: '305' },
  { test: 'repeated-digits', token: '11', room: '303' },
  { test: 'zero-containing', token: '20', room: '100' },
  { test: 'larger-number', token: '999', room: '999' },
]);

/** The four announcement patterns, in the order the collection numbers them. */
const VARIANTS = Object.freeze([
  { key: 'en-with-room', language: 'en', withRoom: true, label: 'English, with room' },
  { key: 'en-no-room', language: 'en', withRoom: false, label: 'English, without room' },
  { key: 'bn-with-room', language: 'bn', withRoom: true, label: 'Bangla, with room' },
  { key: 'bn-no-room', language: 'bn', withRoom: false, label: 'Bangla, without room' },
]);


/** @param {string|Buffer} value */
function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

/**
 * Build a canonical 44-byte PCM header for 16-bit mono audio.
 *
 * Same layout ffmpeg writes for `pcm_s16le`, so the outputs are plain WAVs any
 * player understands.
 *
 * @param {number} dataBytes
 * @param {{sampleRate: number, channels: number, bitsPerSample: number}} format
 */
function wavHeader(dataBytes, format) {
  const blockAlign = format.channels * (format.bitsPerSample / 8);
  const header = Buffer.alloc(44);
  header.write('RIFF', 0, 'ascii');
  header.writeUInt32LE(36 + dataBytes, 4);
  header.write('WAVE', 8, 'ascii');
  header.write('fmt ', 12, 'ascii');
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20); // PCM
  header.writeUInt16LE(format.channels, 22);
  header.writeUInt32LE(format.sampleRate, 24);
  header.writeUInt32LE(format.sampleRate * blockAlign, 28);
  header.writeUInt16LE(blockAlign, 32);
  header.writeUInt16LE(format.bitsPerSample, 34);
  header.write('data', 36, 'ascii');
  header.writeUInt32LE(dataBytes, 40);
  return header;
}

/**
 * Mirror of `toBanglaDigits()` in content.js, used only to render the caption
 * *before* it is compared against the real function's output.
 *
 * @param {string} value
 */
function toBanglaDigits(value) {
  return String(value).replace(/[0-9]/g, (digit) => BN_DIGITS[Number(digit)]);
}

/**
 * Render the expected spoken text from the approved template.
 *
 * Mirrors `buildAnnouncement()`: only `{number}` and `{room}` are substituted,
 * the token number becomes Bangla digits for `bn`, and the room is inserted
 * exactly as supplied (content.js does not convert the room).
 *
 * @param {Record<string, {withRoom: string, noRoom: string}>} templates
 * @param {'en'|'bn'} language
 * @param {string} tokenDigits
 * @param {string|null} roomDigits
 */
function renderExpectedText(templates, language, tokenDigits, roomDigits) {
  const template = roomDigits ? templates[language].withRoom : templates[language].noRoom;
  const number = language === 'bn' ? toBanglaDigits(tokenDigits) : tokenDigits;
  return template.replace('{number}', number).replace('{room}', roomDigits || '');
}

const BN_DIGITS = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'];

const argv = process.argv.slice(2);
const QUIET = argv.includes('--quiet');
const FORCE = argv.includes('--force');

/**
 * Every file under the served audio tree, as `relative path -> sha256`.
 *
 * Used to prove the catalogue was not modified. Includes the lossy originals and
 * the manifest, so the check covers more than the files this tool reads.
 */
function hashAudioTree() {
  const records = {};
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.isFile()) {
        records[path.relative(AUDIO_ROOT, full).split(path.sep).join('/')] = sha256(fs.readFileSync(full));
      }
    }
  };
  walk(AUDIO_ROOT);
  return records;
}

/**
 * Compare two hash maps and return the entries that were added, removed or
 * rewritten.
 *
 * @param {Record<string, string>} before
 * @param {Record<string, string>} after
 */
function diffTrees(before, after) {
  const added = Object.keys(after).filter((key) => !(key in before));
  const removed = Object.keys(before).filter((key) => !(key in after));
  const changed = Object.keys(after).filter((key) => key in before && before[key] !== after[key]);
  return { added, removed, changed, identical: added.length + removed.length + changed.length === 0 };
}

/**
 * Read a master WAV and describe it, refusing anything that is not the delivery
 * contract.
 *
 * @param {string} assetId
 * @param {{masterFile: string, durationSeconds: number}} asset
 */
function loadClip(assetId, asset) {
  const filePath = path.join(AUDIO_ROOT, ...asset.masterFile.split('/'));
  if (!fs.existsSync(filePath)) {
    return { ok: false, assetId, problem: `missing master ${asset.masterFile}` };
  }
  const buffer = fs.readFileSync(filePath);
  const wav = parseWav(buffer);
  if (!wav || !wav.ok) {
    return { ok: false, assetId, problem: `unreadable WAV (${wav ? wav.problems.join('; ') : 'not a RIFF/WAVE file'})` };
  }
  if (wav.format !== CONTRACT.format || wav.channels !== CONTRACT.channels
      || wav.sampleRate !== CONTRACT.sampleRate || wav.bitsPerSample !== CONTRACT.bitsPerSample) {
    return {
      ok: false,
      assetId,
      problem: `format ${wav.format}/${wav.channels}ch/${wav.sampleRate}Hz/${wav.bitsPerSample}-bit is not the 44.1 kHz mono 16-bit PCM contract`,
    };
  }
  const blockAlign = wav.channels * (wav.bitsPerSample / 8);
  const frames = wav.dataSize / blockAlign;
  if (!Number.isInteger(frames) || frames <= 0) {
    return { ok: false, assetId, problem: 'data chunk is not a whole number of sample frames' };
  }
  if (Math.abs(frames / wav.sampleRate - asset.durationSeconds) > 0.01) {
    return {
      ok: false,
      assetId,
      problem: `manifest says ${asset.durationSeconds}s but the file holds ${(frames / wav.sampleRate).toFixed(3)}s`,
    };
  }
  const data = buffer.subarray(wav.dataOffset, wav.dataOffset + wav.dataSize);
  return {
    ok: true,
    assetId,
    asset,
    filePath,
    relativeFile: asset.masterFile,
    buffer,
    wav,
    frames,
    blockAlign,
    sampleRate: wav.sampleRate,
    durationSeconds: frames / wav.sampleRate,
    data,
    dataSha256: sha256(data),
    fileSha256: sha256(buffer),
  };
}

/**
 * Locate the speech inside one clip without altering it.
 *
 * Reports where the recorded speech starts and ends relative to the file, so the
 * report can state exactly how much trailing silence each clip carries. This is
 * measurement only: nothing is trimmed, and the numbers are shown to the reviewer
 * rather than acted on.
 *
 * A sample counts as speech when its magnitude reaches 2% of the clip's own peak
 * (about -34 dBFS relative to that clip), which ignores dither and room tone but
 * still catches soft consonants.
 *
 * @param {{data: Buffer, sampleRate: number}} clip
 */
function analyseSpeech(clip) {
  const { data, sampleRate } = clip;
  const samples = data.length / 2;
  let peak = 0;
  for (let i = 0; i < samples; i += 1) {
    const value = Math.abs(data.readInt16LE(i * 2));
    if (value > peak) peak = value;
  }
  const threshold = Math.max(1, Math.round(peak * 0.02));
  let first = -1;
  let last = -1;
  for (let i = 0; i < samples; i += 1) {
    if (Math.abs(data.readInt16LE(i * 2)) >= threshold) {
      if (first < 0) first = i;
      last = i;
    }
  }
  const total = samples / sampleRate;
  const round = (value) => Math.round(value * 1000) / 1000;
  if (first < 0) {
    return {
      peakDbfs: -Infinity,
      threshold,
      silent: true,
      speechStartSeconds: null,
      speechEndSeconds: null,
      leadingSilenceSeconds: round(total),
      tailSilenceSeconds: round(total),
      totalSeconds: round(total),
    };
  }
  return {
    peakDbfs: Math.round((20 * Math.log10(peak / 32768)) * 10) / 10,
    threshold,
    silent: false,
    speechStartSeconds: round(first / sampleRate),
    speechEndSeconds: round(last / sampleRate),
    leadingSilenceSeconds: round(first / sampleRate),
    tailSilenceSeconds: round((samples - 1 - last) / sampleRate),
    totalSeconds: round(total),
  };
}

/**
 * Ask `content.js` itself what each case should say.
 *
 * Runs in a child process so the expected strings come from the real product
 * module rather than from this tool's template substitution, and so the Node
 * module-type notice for that typeless package stays out of the generator's
 * output.
 *
 * @param {Array<{language: 'en'|'bn', token: string, room: string|null}>} cases
 * @returns {{ok: boolean, results: Array<object>|null, detail: string}}
 */
function verifyWordingWithContentModule(cases) {
  const script = `
    const { buildAnnouncement } = await import(process.argv[1]);
    const cases = JSON.parse(process.argv[2]);
    const out = cases.map((c) => {
      const result = buildAnnouncement({ token: c.token, room: c.room ?? undefined }, c.language);
      return result.ok
        ? { ok: true, text: result.text, tokenNumber: result.fields.tokenNumber, room: result.fields.room, template: result.fields.template }
        : { ok: false, reason: result.reason };
    });
    process.stdout.write(JSON.stringify(out));
  `;

  const result = spawnSync(
    process.execPath,
    ['--disable-warning=MODULE_TYPELESS_PACKAGE_JSON', '--input-type=module', '-e', script,
      pathToFileURL(CONTENT_MODULE).href, JSON.stringify(cases)],
    { encoding: 'utf8', cwd: REPO_ROOT, timeout: 60_000, windowsHide: true },
  );
  if (result.error || result.status !== 0) {
    const why = (result.stderr || '').trim().split(/\r?\n/).slice(0, 3).join(' | ') || `exit ${result.status}`;
    return { ok: false, results: null, detail: `could not run content.js: ${why.slice(0, 300)}` };
  }
  try {
    return { ok: true, results: JSON.parse(result.stdout), detail: 'compared against buildAnnouncement()' };
  } catch {
    return { ok: false, results: null, detail: 'content.js output was not valid JSON' };
  }
}


/**
 * Compose one sample from the byte-identical PCM of its clips.
 *
 * @param {{index: number, caseSpec: {test: string, token: string, room: string},
 *   variant: {key: string, language: 'en'|'bn', withRoom: boolean, label: string},
 *   clips: Map<string, object>, templates: Record<string, object>}} input
 */
function buildSample({ index, caseSpec, variant, clips, templates }) {
  const roomDigits = variant.withRoom ? caseSpec.room : null;
  const plan = planSegments({ language: variant.language, tokenDigits: caseSpec.token, roomDigits });
  if (!plan.ok) return { ok: false, problem: `${variant.key}/${caseSpec.test}: ${plan.detail}` };

  const id = `S${String(index + 1).padStart(2, '0')}-${variant.key}-T${caseSpec.token}${roomDigits ? `-R${roomDigits}` : ''}`;
  const fileName = `${id}.wav`;
  const outPath = path.join(SAMPLES_DIR, fileName);

  const pieces = [];
  const segments = [];
  let frames = 0;
  let byteOffset = 0;

  for (let i = 0; i < plan.segments.length; i += 1) {
    const segment = plan.segments[i];
    const clip = clips.get(segment.assetId);
    if (!clip) return { ok: false, problem: `${id}: clip ${segment.assetId} is not available` };

    const pauseMs = pauseBefore(plan.segments, i, DEFAULT_PAUSE_MS);
    if (pauseMs > 0) {
      const pauseFrames = Math.round((pauseMs / 1000) * clip.sampleRate);
      const silence = Buffer.alloc(pauseFrames * clip.blockAlign);
      pieces.push(silence);
      frames += pauseFrames;
      byteOffset += silence.length;
    }

    pieces.push(clip.data);
    segments.push({
      index: i,
      assetId: segment.assetId,
      role: segment.role,
      sourceFile: clip.relativeFile,
      sourceDataSha256: clip.dataSha256,
      frames: clip.frames,
      durationSeconds: Math.round(clip.durationSeconds * 1000) / 1000,
      pauseBeforeMs: pauseMs,
      outputOffsetBytes: byteOffset,
      outputBytes: clip.data.length,
    });
    frames += clip.frames;
    byteOffset += clip.data.length;
  }

  const data = Buffer.concat(pieces);
  const fileBuffer = Buffer.concat([wavHeader(data.length, CONTRACT), data]);
  fs.mkdirSync(SAMPLES_DIR, { recursive: true });
  const newSha256 = sha256(fileBuffer);
  const existing = fs.existsSync(outPath) ? fs.readFileSync(outPath) : null;
  // The composition is deterministic, so an identical existing sample is left
  // exactly as it is unless --force asks for a rewrite. Nothing is appended or
  // normalised on a second run.
  const reused = Boolean(existing) && !FORCE && sha256(existing) === newSha256;
  if (!reused) fs.writeFileSync(outPath, fileBuffer);

  // Re-read what was actually written and prove every copied range survived
  // byte for byte. This is the "no re-encode" evidence: it is checked in the
  // output instead of being inferred from the code path.
  const written = fs.readFileSync(outPath);
  const wav = parseWav(written);
  const outData = wav && wav.ok ? written.subarray(wav.dataOffset, wav.dataOffset + wav.dataSize) : Buffer.alloc(0);
  const checks = segments.map((segment) => {
    const slice = outData.subarray(segment.outputOffsetBytes, segment.outputOffsetBytes + segment.outputBytes);
    const source = clips.get(segment.assetId).data;
    const outputSha256 = sha256(slice);
    return {
      ...segment,
      outputSha256,
      byteIdentical: slice.equals(source),
      checksumMatches: outputSha256 === segment.sourceDataSha256,
    };
  });

  // Digit sequence: compared against the request, not against the plan, so the
  // check cannot be satisfied by the same code that produced it.

  const tokenDigitClips = [...caseSpec.token].map((digit) => digitAssetId(variant.language, Number(digit)));
  const roomDigitClips = roomDigits ? [...roomDigits].map((digit) => digitAssetId(variant.language, Number(digit))) : [];
  const prefixIndex = plan.segments.findIndex((segment) => segment.role === 'room-prefix');
  const digitSegments = plan.segments
    .map((segment, i) => ({ ...segment, i }))
    .filter((segment) => segment.role === 'digit');
  const actualToken = digitSegments.filter((segment) => prefixIndex < 0 || segment.i < prefixIndex).map((s) => s.assetId);
  const actualRoom = digitSegments.filter((segment) => prefixIndex >= 0 && segment.i > prefixIndex).map((s) => s.assetId);

  const expectedText = renderExpectedText(templates, variant.language, caseSpec.token, roomDigits);
  const decode = verifyDecode(outPath);

  const durationSeconds = Math.round((frames / CONTRACT.sampleRate) * 1000) / 1000;
  const problems = [];
  if (!wav || !wav.ok) problems.push(`written file does not parse: ${wav ? wav.problems.join('; ') : 'not RIFF/WAVE'}`);
  if (wav && wav.dataSize !== data.length) problems.push(`data chunk ${wav.dataSize} != copied ${data.length}`);
  if (!checks.every((check) => check.byteIdentical && check.checksumMatches)) problems.push('a copied PCM range does not match its source');
  if (actualToken.join('|') !== tokenDigitClips.join('|')) problems.push(`token digit sequence ${actualToken.join('+')} != requested ${tokenDigitClips.join('+')}`);
  if (actualRoom.join('|') !== roomDigitClips.join('|')) problems.push(`room digit sequence ${actualRoom.join('+')} != requested ${roomDigitClips.join('+')}`);
  if (decode.available && !decode.verified) problems.push(`decoder check failed: ${decode.detail}`);
  if (wav && Math.abs(wav.durationSeconds - durationSeconds) > 0.005) problems.push('written duration does not match the summed clip frames');

  return {
    ok: problems.length === 0,
    problems,
    record: {
      id,
      file: fileName,
      url: `samples/${fileName}`,
      announcementType: variant.withRoom ? 'with_room' : 'no_room',
      announcementTypeLabel: variant.label,
      language: variant.language,
      test: caseSpec.test,
      token: caseSpec.token,
      room: roomDigits,
      expectedText,
      pauseMs: DEFAULT_PAUSE_MS,
      frames,
      durationSeconds,
      bytes: fileBuffer.length,
      sha256: newSha256,
      reusedOnThisRun: reused,
      segments: checks,
      digitSequence: { token: actualToken, room: actualRoom },
      decode: {
        available: decode.available,
        verified: decode.verified,
        method: decode.method,
        durationMs: decode.probe ? decode.probe.durationMs : null,
        sampleRate: decode.probe ? decode.probe.sampleRate : null,
        channels: decode.probe ? decode.probe.channels : null,
        detail: decode.detail,
      },
    },
  };
}

/**
 * Inputs the preview page must normalise exactly as the product does, recorded so
 * the reviewer can see the rule rather than take it on trust. Informational: the
 * page calls `buildAnnouncement()` itself, so these are observations of the real
 * function, not assertions about this tool.
 */
const NORMALISATION_PROBES = Object.freeze([
  { label: 'token with a doctor fragment (T-3F2A9C-004)', language: 'en', token: 'T-3F2A9C-004', room: '305' },
  { label: 'token with leading zeros (004)', language: 'en', token: '004', room: null },
  { label: 'Bangla digits typed in (০০৪ / ৩০৫)', language: 'bn', token: '০০৪', room: '৩০৫' },
  { label: 'internal identifier (UUID) must be refused', language: 'en', token: '123e4567-e89b-12d3-a456-426614174000', room: null },
  { label: 'letters are not spoken', language: 'bn', token: '4a', room: null },
]);

function main() {
  const started = Date.now();
  const log = (...parts) => { if (!QUIET) console.log(...parts); };

  log('QUE-006 — composing the fixed composed-announcement sample collection');
  log('');

  const manifest = readJson(MANIFEST_PATH);
  const manifestSha256 = sha256(fs.readFileSync(MANIFEST_PATH));
  const assets = Array.isArray(manifest.assets) ? manifest.assets : [];
  const templates = loadApprovedTemplates();
  const baselineBefore = hashAudioTree();
  const baselinePath = path.join(GENERATED_DIR, 'source-baseline.json');
  const previousBaseline = fs.existsSync(baselinePath) ? readJson(baselinePath) : null;

  if (assets.length !== 28) {
    console.error(`FAIL: manifest lists ${assets.length} assets, expected 28`);
    return 1;
  }

  // Load every master, not only the ones this matrix uses: the live preview can
  // ask for any digit in either language, and one broken clip must stop the run
  // now rather than fail mid-review in front of the owner.
  const clips = new Map();
  const clipProblems = [];
  for (const asset of assets) {
    const clip = loadClip(asset.id, asset);
    if (clip.ok) clips.set(asset.id, clip);
    else clipProblems.push(`${asset.id}: ${clip.problem}`);
  }
  log(`  catalogue       : ${assets.length} assets, ${clips.size} masters satisfy the 44.1 kHz / mono / 16-bit PCM contract`);
  log(`  manifest sha256 : ${manifestSha256}`);
  log('  approved wording: read from frontend/lib/announcements/content.js via lib/approved-templates.mjs');
  if (clipProblems.length) {
    for (const problem of clipProblems) console.error(`  FAIL ${problem}`);
    console.error('FAIL: refusing to compose from a catalogue that is not contract-valid');
    return 1;
  }

  // ---- samples -----------------------------------------------------------
  const results = [];
  let index = 0;
  for (const caseSpec of CASES) {
    for (const variant of VARIANTS) {
      results.push(buildSample({ index, caseSpec, variant, clips, templates }));
      index += 1;
    }
  }
  const failures = results.filter((result) => !result.ok);
  if (failures.length) {
    for (const failure of failures) console.error(`  FAIL ${failure.problem}`);
    console.error(`FAIL: ${failures.length} of ${results.length} samples did not compose`);
    return 1;
  }
  const samples = results.map((result) => result.record);
  const copiedRanges = samples.reduce((sum, sample) => sum + sample.segments.length, 0);
  const identicalRanges = samples.reduce(
    (sum, sample) => sum + sample.segments.filter((segment) => segment.byteIdentical && segment.checksumMatches).length,
    0,
  );
  log(`  samples         : ${samples.length}/${CASES.length * VARIANTS.length} composed at a ${DEFAULT_PAUSE_MS} ms junction pause`);
  log(`  clip copies     : ${identicalRanges}/${copiedRanges} PCM ranges byte-identical to their source`);

  // ---- wording -----------------------------------------------------------
  const wordingInputs = samples.map((sample) => ({ language: sample.language, token: sample.token, room: sample.room }));
  const wording = verifyWordingWithContentModule(wordingInputs);
  const wordingChecks = [];
  if (wording.ok) {
    samples.forEach((sample, i) => {
      const actual = wording.results[i];
      wordingChecks.push({
        sampleId: sample.id,
        expectedRendered: sample.expectedText,
        contentModuleText: actual && actual.ok ? actual.text : null,
        contentModuleTemplate: actual && actual.ok ? actual.template : null,
        match: Boolean(actual && actual.ok && actual.text === sample.expectedText),
      });
    });
  }
  const wordingMismatches = wordingChecks.filter((check) => !check.match);
  log(`  wording         : ${wording.ok ? `${wordingChecks.length - wordingMismatches.length}/${wordingChecks.length} captions equal buildAnnouncement()` : wording.detail}`);
  if (!wording.ok || wordingMismatches.length) {
    for (const mismatch of wordingMismatches) {
      console.error(`  FAIL ${mismatch.sampleId}: "${mismatch.expectedRendered}" != "${mismatch.contentModuleText}"`);
    }
    console.error('FAIL: a caption does not match the approved wording');
    return 1;
  }

  const probeResult = verifyWordingWithContentModule(
    NORMALISATION_PROBES.map((probe) => ({ language: probe.language, token: probe.token, room: probe.room })),
  );
  const normalisation = NORMALISATION_PROBES.map((probe, i) => {
    const actual = probeResult.ok ? probeResult.results[i] : null;
    return {
      label: probe.label,
      input: { language: probe.language, token: probe.token, room: probe.room },
      ok: Boolean(actual && actual.ok),
      text: actual && actual.ok ? actual.text : null,
      reason: actual && !actual.ok ? actual.reason : null,
    };
  });

  // ---- catalogue preservation -------------------------------------------
  const baselineAfter = hashAudioTree();
  const treeDiff = diffTrees(baselineBefore, baselineAfter);
  const manifestUnchanged = baselineAfter['manifest.json'] === manifestSha256;
  log(`  catalogue       : ${Object.keys(baselineAfter).length} files under frontend/public/audio, ${treeDiff.identical ? 'none modified by this run' : 'CHANGED'}`);
  log(`  manifest.json   : ${manifestUnchanged ? 'untouched' : 'CHANGED'}`);
  if (!treeDiff.identical || !manifestUnchanged) {
    for (const key of [...treeDiff.added, ...treeDiff.removed, ...treeDiff.changed]) console.error(`  FAIL audio tree: ${key}`);
    console.error('FAIL: the audio catalogue changed while composing; the samples cannot be trusted');
    return 1;
  }

  const sinceLastRun = previousBaseline && previousBaseline.files
    ? diffTrees(previousBaseline.files, baselineAfter)
    : null;

  // ---- artefacts ---------------------------------------------------------
  const generatedAt = new Date().toISOString();
  const clipAnalysis = assets.map((asset) => {
    const clip = clips.get(asset.id);
    const speech = analyseSpeech(clip);
    return {
      assetId: asset.id,
      masterFile: asset.masterFile,
      spokenText: asset.spokenText,
      frames: clip.frames,
      durationSeconds: Math.round(clip.durationSeconds * 1000) / 1000,
      dataSha256: clip.dataSha256,
      ...speech,
      usedBySamples: samples.filter((sample) => sample.segments.some((segment) => segment.assetId === asset.id)).length,
    };
  });

  const totalBytes = samples.reduce((sum, sample) => sum + sample.bytes, 0);
  const silenceTail = clipAnalysis.filter((clip) => (clip.tailSilenceSeconds || 0) > 0.5);

  writeJson(path.join(GENERATED_DIR, 'samples.json'), {
    tool: 'scripts/que-006-audio/preview/compose-wav.mjs',
    generatedAt,
    pauseMs: DEFAULT_PAUSE_MS,
    pauseRule: 'No pause is inserted before the first clip or before a bound suffix clip (room-locative, room-suffix, no-room).',
    manifestSha256,
    contract: CONTRACT,
    summary: {
      cases: CASES.length,
      variants: VARIANTS.length,
      samples: samples.length,
      totalBytes,
      copiedRanges,
      identicalRanges,
      wordingChecks: wordingChecks.length,
      wordingMismatches: wordingMismatches.length,
      decoderVerified: samples.filter((sample) => sample.decode.verified).length,
      decoderAvailable: samples.some((sample) => sample.decode.available),
      catalogueFilesHashed: Object.keys(baselineAfter).length,
      catalogueUnchanged: treeDiff.identical,
    },
    wordingChecks,
    normalisationProbes: normalisation,
    samples,
  });

  writeJson(path.join(GENERATED_DIR, 'clip-analysis.json'), {
    tool: 'scripts/que-006-audio/preview/compose-wav.mjs',
    generatedAt,
    method: 'Speech bounds measured at 2% of each clip peak (~-34 dBFS relative). Measurement only: nothing was trimmed.',
    clips: clipAnalysis,
    clipsWithTailSilenceOver500ms: silenceTail.map((clip) => ({
      assetId: clip.assetId,
      durationSeconds: clip.durationSeconds,
      speechEndSeconds: clip.speechEndSeconds,
      tailSilenceSeconds: clip.tailSilenceSeconds,
    })),
  });

  writeJson(baselinePath, {
    tool: 'scripts/que-006-audio/preview/compose-wav.mjs',
    takenAt: generatedAt,
    root: 'frontend/public/audio',
    files: baselineAfter,
  });

  const pageAssets = assets.map((asset) => {
    const clip = clips.get(asset.id);
    const speech = analyseSpeech(clip);
    return {
      id: asset.id,
      language: asset.language,
      category: asset.category,
      spokenText: asset.spokenText,
      masterFile: asset.masterFile,
      url: `audio/${asset.masterFile}`,
      durationSeconds: Math.round(clip.durationSeconds * 1000) / 1000,
      frames: clip.frames,
      speech: {
        speechStartSeconds: speech.speechStartSeconds,
        speechEndSeconds: speech.speechEndSeconds,
        tailSilenceSeconds: speech.tailSilenceSeconds,
      },
      technicalValidationStatus: asset.technicalValidationStatus,
      humanReviewStatus: asset.humanReviewStatus,
    };
  });

  writeJson(path.join(GENERATED_DIR, 'data.json'), {
    tool: 'scripts/que-006-audio/preview/compose-wav.mjs',
    generatedAt,
    contract: CONTRACT,
    pauseMsDefault: DEFAULT_PAUSE_MS,
    pauseOptionsMs: PAUSE_OPTIONS_MS,
    pauseRule: 'The junction pause is added before every clip except the first and before bound suffix clips, which are always butted directly. It never modifies a file.',
    maxDigits: MAX_DIGITS,
    templates,
    manifest: {
      path: 'frontend/public/audio/manifest.json',
      sha256: manifestSha256,
      generatedAt: manifest.generatedAt,
      assets: assets.length,
      complete: manifest.summary ? manifest.summary.complete : null,
      humanApproved: manifest.summary ? manifest.summary.humanApproved : null,
    },
    summary: {
      samples: samples.length,
      totalBytes,
      catalogueFilesHashed: Object.keys(baselineAfter).length,
      catalogueUnchanged: treeDiff.identical,
      decoderAvailable: samples.some((sample) => sample.decode.available),
    },
    assets: pageAssets,
    samples: samples.map((sample) => ({
      id: sample.id,
      url: `samples/${sample.file}`,
      language: sample.language,
      announcementType: sample.announcementType,
      announcementTypeLabel: sample.announcementTypeLabel,
      test: sample.test,
      token: sample.token,
      room: sample.room,
      expectedText: sample.expectedText,
      frames: sample.frames,
      durationSeconds: sample.durationSeconds,
      sha256: sample.sha256,
      segments: sample.segments.map((segment) => ({
        assetId: segment.assetId,
        role: segment.role,
        pauseBeforeMs: segment.pauseBeforeMs,
        durationSeconds: segment.durationSeconds,
      })),
    })),
  });

  log('');
  log(`  outputs         : ${path.relative(REPO_ROOT, SAMPLES_DIR).split(path.sep).join('/')}/ (${samples.length} WAVs, ${(totalBytes / 1024 / 1024).toFixed(2)} MB)`);
  log(`  index           : ${path.relative(REPO_ROOT, path.join(GENERATED_DIR, 'samples.json')).split(path.sep).join('/')}`);
  log(`  preview data    : ${path.relative(REPO_ROOT, path.join(GENERATED_DIR, 'data.json')).split(path.sep).join('/')}`);
  if (sinceLastRun && !sinceLastRun.identical) {
    log(`  since last run  : ${sinceLastRun.added.length} added, ${sinceLastRun.removed.length} removed, ${sinceLastRun.changed.length} changed`);
  } else if (sinceLastRun) {
    log('  since last run  : catalogue identical');
  }
  log('');
  log(`PASS — ${samples.length} samples composed, ${identicalRanges}/${copiedRanges} clip copies byte-identical, `
    + `${wordingChecks.length}/${wordingChecks.length} captions equal buildAnnouncement(), catalogue untouched `
    + `(${Date.now() - started} ms)`);
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exitCode = main();
}







