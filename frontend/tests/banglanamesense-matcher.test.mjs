/* BanglaNameSense — matching engine and ranking tests.
 *
 * Uses the shipped dataset, so every assertion is about real data.
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { createNameIndex, RANK, DEFAULT_MAX_SUGGESTIONS } from '../lib/bangla-name-sense/matcher.js';
import { normalizeBangla } from '../lib/bangla-name-sense/normalize.js';
import { buildDataset } from '../lib/bangla-name-sense/dataset.js';

const raw = JSON.parse(readFileSync(new URL('../data/bangla_name_sense.json', import.meta.url), 'utf8'));
const index = buildDataset(raw).index;
const names = (results) => results.map((r) => r.bn);

test('Bangla prefix matching returns the expected names', () => {
  const results = index.search('রফিক রহমান');
  assert.equal(results[0].bn, 'রফিক রহমান');
  assert.equal(results[0].score, RANK.EXACT);

  const prefix = index.search('রফিক');
  assert.ok(prefix.length > 0);
  assert.ok(prefix.every((r) => r.bn.startsWith('রফিক')));
  assert.ok(prefix.every((r) => r.score === RANK.PREFIX));
});

test('Bangla matching is Unicode-normalized (nukta forms, NFC, zero-width chars)', () => {
  // য় can arrive as U+09DF (composed) or U+09AF U+09BC (decomposed).
  const composed = 'রিয়া';
  const decomposed = 'রি\u09AF\u09BCা';
  assert.equal(normalizeBangla(composed), normalizeBangla(decomposed));
  assert.deepEqual(names(index.search(composed)), names(index.search(decomposed)));

  // A stray zero-width joiner must not break a prefix match.
  assert.ok(index.search('\u200Dরফিক').length > 0);
  assert.equal(normalizeBangla('  রফিক   রহমান '), 'রফিক রহমান');
});

test('multi-word matching works when words are abbreviated', () => {
  // "রফি খা" is not a prefix of "রফিক খান", but both words prefix its words.
  const results = index.search('রফি খা');
  const match = results.find((r) => r.bn === 'রফিক খান');
  assert.ok(match, `expected রফিক খান in ${JSON.stringify(names(results))}`);
  assert.equal(match.score, RANK.WORD);
});

test('multi-word matching is order-sensitive and does not match reversed words', () => {
  assert.deepEqual(index.search('খান রফিক'), []);
});

test('English alias matching works and is case-insensitive', () => {
  for (const query of ['rof', 'ROF', 'RoF']) {
    const results = index.search(query, { maxSuggestions: 50 });
    assert.ok(results.length > 0, `no result for ${query}`);
    assert.ok(results.every((r) => r.score === RANK.ALIAS), `${query} must rank as an alias match`);
    assert.ok(results.some((r) => r.bn === 'রফিক রহমান'), `${query} must include রফিক রহমান`);
    assert.deepEqual(results, index.search('rof', { maxSuggestions: 50 }), 'case must not change results');
  }
  // Multi-word aliases match word prefixes too (case-insensitively).
  const multi = index.search('rof rah', { maxSuggestions: 50 });
  assert.ok(multi.some((r) => r.bn === 'রফিক রহমান'));
  assert.deepEqual(multi, index.search('ROF RAH', { maxSuggestions: 50 }));
});

test('English alias never outranks a Bangla prefix match', () => {
  const results = index.search('রফিক');
  const firstAlias = results.findIndex((r) => r.score === RANK.ALIAS);
  const lastBangla = results.map((r) => r.score === RANK.PREFIX).lastIndexOf(true);
  if (firstAlias !== -1) assert.ok(lastBangla < firstAlias);
});

test('duplicate Bangla names are suppressed without losing their aliases', () => {
  // "রফিকা রহমান" occurs twice in the source (718 records, 701 distinct).
  const results = index.search('রফিকা রহমান');
  const occurrences = results.filter((r) => r.bn === 'রফিকা রহমান');
  assert.equal(occurrences.length, 1);
  const entry = index.entries.find((e) => e.bn === 'রফিকা রহমান');
  assert.ok(entry.aliases.length >= 1);
});

test('every displayed suggestion is unique', () => {
  for (const query of ['র', 'রফ', 'আ', 'মো', 'rof']) {
    const got = names(index.search(query, { maxSuggestions: 50 }));
    assert.equal(new Set(got).size, got.length, `duplicates for ${query}`);
  }
});

test('empty and unmatched queries return nothing and do not throw', () => {
  for (const query of ['', '   ', null, undefined, 'zzzzzz', '12345', '!!!']) {
    assert.deepEqual(index.search(query), []);
  }
});

test('maxSuggestions is configurable and defaults to 8', () => {
  assert.equal(index.search('র').length, DEFAULT_MAX_SUGGESTIONS);
  assert.equal(index.search('র', { maxSuggestions: 3 }).length, 3);
  assert.equal(index.search('র', { maxSuggestions: 25 }).length, 25);
});

test('minQueryLength can be raised to suppress single-character searches', () => {
  assert.equal(index.search('র', { minQueryLength: 2 }).length, 0);
  assert.ok(index.search('রফ', { minQueryLength: 2 }).length > 0);
});

test('ranking is deterministic and independent of source order', () => {
  const a = names(index.search('রফিক', { maxSuggestions: 10 }));
  const b = names(index.search('রফিক', { maxSuggestions: 10 }));
  assert.deepEqual(a, b);

  const reversed = createNameIndex(raw.names.slice().reverse());
  assert.deepEqual(names(reversed.search('রফিক', { maxSuggestions: 10 })), a);
  assert.deepEqual(names(reversed.search('rof', { maxSuggestions: 10 })), names(index.search('rof', { maxSuggestions: 10 })));
});

test('results never expose gender or any other dataset metadata', () => {
  for (const result of index.search('রফিক')) {
    assert.deepEqual(Object.keys(result).sort(), ['bn', 'en', 'match', 'score']);
  }
});

test('local search is fast enough for per-keystroke use', () => {
  const started = process.hrtime.bigint();
  for (let i = 0; i < 200; i += 1) index.search('রফিক র');
  const ms = Number(process.hrtime.bigint() - started) / 1e6;
  assert.ok(ms < 2000, `200 searches took ${ms.toFixed(1)}ms`);
});
