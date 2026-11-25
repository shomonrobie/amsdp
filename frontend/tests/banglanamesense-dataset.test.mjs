/* BanglaNameSense — dataset validation tests.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

import { validateDataset } from '../lib/bangla-name-sense/validate-dataset.js';
import { buildDataset, DATASET_SOURCE } from '../lib/bangla-name-sense/dataset.js';

const DATASET_URL = new URL('../data/bangla_name_sense.json', import.meta.url);
const rawText = readFileSync(DATASET_URL, 'utf8');
const raw = JSON.parse(rawText);

test('shipped dataset passes structural validation', () => {
  const result = validateDataset(raw);
  assert.deepEqual(result.errors, []);
  assert.equal(result.ok, true);
});

test('declared total_count matches the number of records (718)', () => {
  assert.equal(typeof raw.total_count, 'number');
  assert.equal(raw.total_count, 718);
  assert.equal(raw.names.length, 718);
  assert.equal(DATASET_SOURCE.records, raw.names.length);
});

test('701 distinct Bangla names; duplicates reported, source left untouched', () => {
  const { stats } = validateDataset(raw);
  assert.equal(stats.distinctBangla, 701);
  assert.equal(stats.duplicates, 17);
  assert.equal(DATASET_SOURCE.distinctBangla, stats.distinctBangla);
  // The validator must never mutate or rebuild the source array.
  assert.equal(raw.names.length, 718);
});

test('every record has a non-empty bn in Bengali script and a non-empty en alias', () => {
  const { stats } = validateDataset(raw);
  assert.equal(stats.banglaNames, 718);
  assert.equal(stats.withEnglishAlias, 718);
  for (const record of raw.names) {
    assert.ok(['en', 'bn', 'gender'].every((k) => k in record), `unexpected shape: ${JSON.stringify(record)}`);
    assert.match(record.bn, /[\u0980-\u09FF]/);
    assert.doesNotMatch(record.en, /[\u0980-\u09FF]/);
  }
});

test('dataset carries no patient or private application data', () => {
  for (const record of raw.names) {
    for (const key of Object.keys(record)) {
      assert.ok(['en', 'bn', 'gender'].includes(key),
        `record must not carry patient data field "${key}"`);
    }
  }
});

/* The dataset is authored with LF line endings. A checkout can hand us CRLF
 * instead — this repository sets core.autocrlf=true and carries no
 * .gitattributes — which changes the bytes without changing the content. Hash
 * and measure the LF-canonical form so the digest in DATASET_SOURCE stays
 * authoritative on every platform; a genuine content change still fails,
 * because it survives normalisation. */
const canonicalBytes = Buffer.from(rawText.replace(/\r\n/g, '\n'), 'utf8');

test('dataset bytes match the hash recorded in DATASET_SOURCE', () => {
  const sha256 = createHash('sha256').update(canonicalBytes).digest('hex');
  assert.equal(sha256, DATASET_SOURCE.sha256);
  assert.equal(canonicalBytes.length, DATASET_SOURCE.bytes);
});

test('validator rejects malformed datasets instead of accepting them', () => {
  assert.equal(validateDataset(null).ok, false);
  assert.equal(validateDataset([]).ok, false);
  assert.equal(validateDataset({ names: 'not-an-array' }).ok, false);
  assert.equal(validateDataset({ total_count: 2, names: [{ bn: 'রফিক', en: 'Rofik' }] }).ok, false);
  assert.equal(validateDataset({ total_count: 1, names: [{ bn: 'Rofik', en: 'Rofik' }] }).ok, false);
  assert.equal(validateDataset({ total_count: 1, names: [{ bn: 'রফিক' }] }).ok, false);
  assert.equal(validateDataset({ total_count: 1, names: [{ bn: 'রফিক', en: 'Rofik', mobile: '01700000000' }] }).ok, false);
});

test('buildDataset turns the shipped file into a 701-entry search index', () => {
  const built = buildDataset(raw);
  assert.equal(built.ok, true);
  assert.equal(built.index.size, 701);
  assert.equal(built.index.sourceCount, 718);
  assert.ok(built.index.search('রফিক').length > 0);
});

test('a broken dataset disables suggestions instead of breaking patient registration', () => {
  const built = buildDataset({ names: 'nope' });
  assert.equal(built.ok, false);
  assert.equal(built.index.size, 0);
  assert.deepEqual(built.index.search('রফিক'), []);
});
