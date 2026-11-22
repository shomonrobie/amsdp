#!/usr/bin/env node
/**
 * QUE-006 — build the human-review record for the composed samples.
 *
 * Emits `generated/review-template.csv`: one row per generated sample, with the
 * facts a reviewer must not retype (id, caption, duration, hash, clip count)
 * pre-filled and every judgement column left empty. It is derived from
 * `generated/samples.json`, so a re-run of `compose-wav.mjs` followed by this
 * script cannot produce a record that contradicts the audio.
 *
 * The judgements are deliberately blank: this script does not review anything,
 * and an empty verdict means "not yet listened to", never "fine".
 *
 * Usage:
 *   node scripts/que-006-audio/preview/make-review-template.mjs
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const GENERATED_DIR = path.join(here, 'generated');
const SAMPLES_PATH = path.join(GENERATED_DIR, 'samples.json');
const TEMPLATE_PATH = path.join(GENERATED_DIR, 'review-template.csv');
const FIELD_GUIDE_PATH = path.join(GENERATED_DIR, 'review-template.md');

/**
 * The record. Facts first, then one blank block of judgements, then a verdict
 * per row. Column names are stable: the preview page renders its help text by
 * reading this header row.
 */
const COLUMNS = Object.freeze([
  'sample_number',
  'sample_id',
  'language',
  'announcement_type',
  'token',
  'room',
  'expected_text',
  'duration_seconds',
  'sha256_12',
  'segment_count',
  'verdict',
  'intelligibility_1_5',
  'pronunciation_1_5',
  'natural_prosody_1_5',
  'digit_clarity_1_5',
  'room_clarity_1_5',
  'junction_pause_ok',
  'audible_artefacts',
  'observations',
  'defect_severity',
  'follow_up_action',
  'reviewer',
  'review_date',
]);

/** Columns the reviewer fills in; everything else is pre-filled fact. */
const JUDGEMENT_COLUMNS = new Set([
  'verdict',
  'intelligibility_1_5',
  'pronunciation_1_5',
  'natural_prosody_1_5',
  'digit_clarity_1_5',
  'room_clarity_1_5',
  'junction_pause_ok',
  'audible_artefacts',
  'observations',
  'defect_severity',
  'follow_up_action',
  'reviewer',
  'review_date',
]);

/**
 * RFC 4180 field: quote when the value contains a comma, quote, CR or LF.
 * @param {unknown} value
 * @returns {string}
 */
function csvField(value) {
  const text = value == null ? '' : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** @param {object} sample @param {number} position @returns {object} */
function rowFor(sample, position) {
  return {
    sample_number: position + 1,
    sample_id: sample.id,
    language: sample.language,
    announcement_type: sample.announcementType,
    token: sample.token,
    room: sample.room == null ? '' : sample.room,
    expected_text: sample.expectedText,
    duration_seconds: Number(sample.durationSeconds).toFixed(3),
    sha256_12: String(sample.sha256).slice(0, 12),
    segment_count: sample.segments.length,
  };
}


/** @type {Record<string, string>} */
const GUIDE = {
  sample_number: 'Row number 1–20, stable across regenerations.',
  sample_id: 'The sample id — the file name without `.wav`.',
  language: '`en` or `bn`.',
  announcement_type: '`with_room` or `no_room`.',
  token: 'Token number spoken.',
  room: 'Room number spoken (empty for no-room samples).',
  expected_text: 'The approved wording from `buildAnnouncement()`.',
  duration_seconds: 'Duration of the written WAV, from its own frame count.',
  sha256_12: 'First 12 hex characters of the file SHA-256 — ids the bytes reviewed.',
  segment_count: 'Number of clips concatenated.',
  verdict: '`pass`, `fail`, or `needs-fix`.',
  intelligibility_1_5: '1 unintelligible … 5 effortlessly understood over a clinic speaker.',
  pronunciation_1_5: '1 wrong word or digit … 5 correct and natural. Bangla needs a fluent speaker.',
  natural_prosody_1_5: '1 robotic or wrongly stressed … 5 like a person at a desk.',
  digit_clarity_1_5: '1 digits run together or clipped … 5 every digit separate.',
  room_clarity_1_5: '1 room number unclear … 5 unmistakable, or `n/a`.',
  junction_pause_ok: '`yes` if the joins sound right at 0 ms, `no` if a pause is needed.',
  audible_artefacts: '`none`, `clipping`, `noise`, `other` — and where.',
  observations: 'What you actually heard, in your own words.',
  defect_severity: '`none`, `minor`, or `major`.',
  follow_up_action: '`nothing`, or the asset to re-record and why.',
  reviewer: 'Your name.',
  review_date: 'Date of the listening session, `YYYY-MM-DD`.',
};

/**
 * The reviewer's instructions, written next to the CSV so the method does not
 * live only in the report.
 * @param {object} payload
 * @returns {string}
 */
function fieldGuide(payload) {
  const en = payload.samples.filter((sample) => sample.language === 'en').length;
  const bn = payload.samples.filter((sample) => sample.language === 'bn').length;
  return `# QUE-006 — human listening review record

Generated ${payload.generatedAt} from \`generated/samples.json\`
(manifest sha256 \`${payload.manifestSha256}\`).

The companion file is \`review-template.csv\`: ${payload.samples.length} rows, one per composed
sample. Facts are pre-filled; every judgement cell is empty, and an empty cell means
**not yet listened to** — never "accept".

## How to run the session

1. Start the preview page and listen: \`node scripts/que-006-audio/preview/server.mjs\`,
   then open the printed URL.
2. Play a sample, read its caption, and fill that row's judgement columns.
3. Compose a few tokens and rooms of your own on the same page. If a hand-made
   announcement sounds wrong but the samples do not, say so in \`observations\`.
4. Use the timeline under each sample to name the exact clip when something fails.
5. Have a native or fluent Bangla speaker review the ${bn} \`bn\` rows independently.

## Columns

| Column | Pre-filled? | What it asks for |
|---|---|---|
${COLUMNS.map((column) => `| \`${column}\` | ${JUDGEMENT_COLUMNS.has(column) ? 'no' : 'yes'} | ${GUIDE[column] || ''} |`).join('\n')}

## What a signed row means

\`verdict = pass\` plus a reviewer name states that **that one composed sample**, as heard
on that device, sounded correct. It does not approve an asset by itself: an asset is
reviewed only when every sample containing it was listened to, and the manifest's
\`humanReviewStatus\` may only be changed by the process that owns it — not by this
template and not by the preview page.

## Current state

- Assets: 28 delivered, \`humanReviewStatus: pending\` for all of them.
- Samples: ${payload.samples.length} composed (${en} English, ${bn} Bangla).
- Human review: **not performed**. No row is signed and no verdict exists.
`;
}


function main() {
  console.log('QUE-006 — building the human-review record for the composed samples');

  if (!fs.existsSync(SAMPLES_PATH)) {
    console.error(`\n  ${SAMPLES_PATH} is missing. Run "node scripts/que-006-audio/preview/compose-wav.mjs" first.\n`);
    process.exitCode = 1;
    return;
  }

  const payload = JSON.parse(fs.readFileSync(SAMPLES_PATH, 'utf8'));
  const samples = payload.samples || [];
  if (samples.length === 0) {
    console.error('\n  samples.json contains no samples; nothing to write.\n');
    process.exitCode = 1;
    return;
  }

  const rows = samples.map(rowFor);

  // The record must not carry a judgement: prove the blank columns are blank
  // rather than trusting that they were left alone.
  for (const [index, row] of rows.entries()) {
    for (const column of JUDGEMENT_COLUMNS) {
      if (column in row) throw new Error(`row ${index + 1} pre-fills "${column}"`);
    }
    for (const column of COLUMNS) {
      if (!JUDGEMENT_COLUMNS.has(column) && (row[column] === undefined || row[column] === null)) {
        throw new Error(`row ${index + 1} has no value for "${column}"`);
      }
    }
  }

  const lines = [COLUMNS.join(',')];
  for (const row of rows) {
    lines.push(COLUMNS.map((column) => csvField(row[column])).join(','));
  }

  // A UTF-8 BOM so Excel opens the Bangla captions correctly; browsers strip it.
  fs.writeFileSync(TEMPLATE_PATH, `\uFEFF${lines.join('\r\n')}\r\n`, 'utf8');
  fs.writeFileSync(FIELD_GUIDE_PATH, fieldGuide(payload), 'utf8');

  const en = samples.filter((sample) => sample.language === 'en').length;
  const bn = samples.filter((sample) => sample.language === 'bn').length;

  console.log('');
  console.log(`  source          : ${path.relative(process.cwd(), SAMPLES_PATH)} (${samples.length} samples, ${en} English, ${bn} Bangla)`);
  console.log(`  columns         : ${COLUMNS.length} (${COLUMNS.length - JUDGEMENT_COLUMNS.size} pre-filled facts, ${JUDGEMENT_COLUMNS.size} blank judgements)`);
  console.log(`  rows            : ${rows.length}, every judgement cell empty`);
  console.log(`  record          : ${path.relative(process.cwd(), TEMPLATE_PATH)}`);
  console.log(`  field guide     : ${path.relative(process.cwd(), FIELD_GUIDE_PATH)}`);
  console.log('');
  console.log('  No verdict is claimed: this file is a blank form for a human, not a review.');
  console.log('');
}

main();
