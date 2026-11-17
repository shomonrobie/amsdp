/* Symptom catalogue search — ranking, bilingual matching, context tie-break.
 *
 * AMSDP-SYMPTOM-01.  These are assertions about *behaviour*, not about the
 * implementation: they fix what a receptionist must be able to type and what
 * the ranking may and may not do.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import { RANK, createCatalogueIndex, textKey } from '../lib/symptom-catalogue/matcher.js';

/* A small fixture that mirrors the real seeded catalogue's shape — names in
 * both scripts, synonyms in both scripts, speciality hints, sort order. */
const CATALOGUE = [
  {
    id: 's-headache', code: 'headache', name_en: 'Headache', name_bn: 'মাথাব্যথা',
    synonyms_en: ['head pain'], synonyms_bn: ['মাথা ব্যথা'],
    category: 'neurological', specialty_hints: ['medicine'], sort_order: 10,
    status: 'active',
  },
  {
    id: 's-dizziness', code: 'dizziness', name_en: 'Dizziness',
    name_bn: 'মাথা ঘোরা',
    synonyms_en: ['giddiness'], synonyms_bn: ['মাথা ঘুরানো'],
    category: 'neurological', specialty_hints: ['medicine'], sort_order: 20,
    status: 'active',
  },
  {
    id: 's-cough', code: 'cough', name_en: 'Cough', name_bn: 'কাশি',
    synonyms_en: ['coughing'], synonyms_bn: ['শুকনো কাশি'],
    category: 'respiratory', specialty_hints: ['medicine', 'pediatrics'],
    sort_order: 30, status: 'active',
  },
  {
    id: 's-chest', code: 'chest_pain', name_en: 'Chest pain',
    name_bn: 'বুকে ব্যথা',
    synonyms_en: ['chest tightness'], synonyms_bn: ['বুকে চাপ'],
    category: 'cardiovascular', specialty_hints: ['cardiology'],
    sort_order: 40, status: 'active',
  },
  {
    id: 's-back', code: 'back_pain', name_en: 'Back pain', name_bn: 'কোমর ব্যথা',
    synonyms_en: ['backache'], synonyms_bn: ['পিঠে ব্যথা'],
    category: 'musculoskeletal', specialty_hints: ['orthopedics'],
    sort_order: 50, status: 'active',
  },
  {
    id: 's-itching', code: 'itching', name_en: 'Itching', name_bn: 'চুলকানি',
    synonyms_en: ['itchy skin'], synonyms_bn: ['শরীর চুলকায়'],
    category: 'skin', specialty_hints: ['dermatology'], sort_order: 60,
    status: 'active',
  },
  {
    id: 's-retired', code: 'retired_entry', name_en: 'Retired entry',
    name_bn: 'বন্ধ এন্ট্রি', synonyms_en: [], synonyms_bn: [],
    category: 'general', specialty_hints: [], sort_order: 70,
    status: 'inactive',
  },
];

const ids = (results) => results.map((result) => result.id);
const build = () => createCatalogueIndex(CATALOGUE);

test('the index skips retired entries and keeps the rest', () => {
  const index = build();
  assert.equal(index.size, 6);
  assert.ok(!ids(index.search('retired')).includes('s-retired'));
  // ...unless an admin screen asks for them explicitly.
  const withRetired = createCatalogueIndex(CATALOGUE, { includeInactive: true });
  assert.equal(withRetired.size, 7);
});

test('Bangla name search finds the entry', () => {
  const results = build().search('মাথাব্যথা');
  assert.equal(results[0].id, 's-headache');
  assert.equal(results[0].rank, RANK.EXACT);
  assert.equal(results[0].match, 'name_bn');
});

test('English name search finds the same entry', () => {
  const results = build().search('headache');
  assert.equal(results[0].id, 's-headache');
  assert.equal(results[0].rank, RANK.EXACT);
  assert.equal(results[0].match, 'name_en');
});

test('Bangla synonyms find the canonical symptom', () => {
  const results = build().search('মাথা ব্যথা');
  assert.equal(results[0].id, 's-headache');
  assert.equal(results[0].match, 'synonym_bn');
});

test('English synonyms find the canonical symptom', () => {
  const results = build().search('head pain');
  assert.equal(results[0].id, 's-headache');
  assert.equal(results[0].match, 'synonym_en');
});

test('partial terms give relevant suggestions in both scripts', () => {
  const index = build();
  const bangla = ids(index.search('মাথা'));
  assert.ok(bangla.includes('s-headache'));
  assert.ok(bangla.includes('s-dizziness'));
  assert.deepEqual(ids(index.search('cou')), ['s-cough']);
});

test('a single word matches inside a multi-word name', () => {
  const results = ids(build().search('pain'));
  assert.ok(results.includes('s-headache'), 'head pain');
  assert.ok(results.includes('s-chest'), 'chest pain');
  assert.ok(results.includes('s-back'), 'back pain');
});

test('search is case-, whitespace- and zero-width-insensitive', () => {
  const index = build();
  assert.deepEqual(ids(index.search('HEADACHE')), ['s-headache']);
  assert.deepEqual(ids(index.search('  headache  ')), ['s-headache']);
  assert.deepEqual(ids(index.search('head\u200Bache')), ['s-headache']);
});

test('search reuses BanglaNameSense Bengali normalisation (nukta composition)', () => {
  // "ড়" typed by a keyboard as ড + ় must normalise to the same key as the
  // precomposed U+09DC — the rule lives in bangla-name-sense/normalize.js.
  const composed = 'কো\u09DC';
  const decomposed = 'কো\u09A1\u09BC';
  assert.equal(textKey(composed), textKey(decomposed));
});

test('an unknown query returns nothing, and an empty query browses', () => {
  const index = build();
  assert.deepEqual(index.search('zzzzz'), []);
  const browse = index.search('');
  assert.equal(browse.length, 6);
  assert.deepEqual(ids(browse).slice(0, 3), ['s-headache', 's-dizziness', 's-cough']);
  // Browsing is a list of candidates, never a selection.
  assert.equal(browse[0].rank, RANK.NONE);
});

test('maxSuggestions limits the list', () => {
  assert.equal(build().search('', { maxSuggestions: 2 }).length, 2);
});

test('already-selected entries are excluded from suggestions', () => {
  const results = build().search('মাথা', { excludeIds: ['s-headache'] });
  assert.ok(!ids(results).includes('s-headache'));
  assert.ok(ids(results).includes('s-dizziness'));
});

test('the doctor speciality may reorder equal matches, never a better one', () => {
  const plain = ids(build().search('pain'));
  const ortho = ids(build().search('pain', { contextSpecialtyCodes: ['orthopedics'] }));
  // All three match equally well, so the catalogue's own commonness order wins.
  assert.deepEqual(plain, ['s-headache', 's-chest', 's-back']);
  // Orthopedics lifts back pain to the top of that equal-ranked group...
  assert.equal(ortho[0], 's-back');
  // ...and removes nothing: the set is identical, only the order changed.
  assert.deepEqual([...ortho].sort(), [...plain].sort());
});

test('context cannot promote a worse textual match', () => {
  // "কাশি" is the only exact match; a cardiology context must not displace it.
  const withContext = build().search('কাশি', { contextSpecialtyCodes: ['cardiology'] });
  assert.equal(withContext[0].id, 's-cough');
  assert.equal(withContext[0].rank, RANK.EXACT);
});

test('a symptom without the doctor speciality stays searchable and selectable', () => {
  const results = build().search('চুলকানি', { contextSpecialtyCodes: ['cardiology'] });
  assert.equal(results[0].id, 's-itching');
  assert.equal(results[0].context, false);
});

test('ranking is deterministic', () => {
  const index = build();
  assert.deepEqual(index.search('মাথা'), index.search('মাথা'));
  assert.deepEqual(
    index.search('pain', { contextSpecialtyCodes: ['orthopedics'] }),
    index.search('pain', { contextSpecialtyCodes: ['orthopedics'] }),
  );
});

test('comma/Tab commit resolves only an unambiguous entry', () => {
  const index = build();
  assert.equal(index.resolveCommit('মাথাব্যথা').entry.id, 's-headache');
  assert.equal(index.resolveCommit('মাথাব্যথা').reason, 'exact');
  // Two prefix matches: the control must not guess which complaint it is.
  assert.equal(index.resolveCommit('মাথা').entry, null);
  assert.equal(index.resolveCommit('মাথা').reason, 'ambiguous');
  // A single partial match is unambiguous.
  assert.equal(index.resolveCommit('coughi').entry.id, 's-cough');
  assert.equal(index.resolveCommit('coughi').reason, 'only-match');
  assert.equal(index.resolveCommit('zzzz').entry, null);
  assert.equal(index.resolveCommit('').reason, 'empty');
});

test('the index tolerates a malformed catalogue instead of throwing', () => {
  const index = createCatalogueIndex([
    null,
    {},
    { id: '', name_en: 'No id' },
    { id: 'ok', name_en: 'Ok', name_bn: 'ঠিক' },
  ]);
  assert.equal(index.size, 1);
  assert.equal(ids(index.search('ok'))[0], 'ok');
});

