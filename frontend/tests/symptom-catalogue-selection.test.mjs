/* Symptom selection — the pure rules behind the picker.
 *
 * AMSDP-SYMPTOM-01.  These pin the contract the UI depends on: no implicit
 * selection, no duplicates, no more than the cap, and a payload that keeps the
 * catalogue/free-text distinction the server records.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import { createCatalogueIndex } from '../lib/symptom-catalogue/matcher.js';
import {
  DEFAULT_MAX_SYMPTOMS, addCatalogue, addFreeText, chipKey, chipsOf,
  commitFromQuery, countOf, emptySelection, hasRoom, isSelected, removeChip,
  toPayload,
} from '../lib/symptom-catalogue/selection.js';

const CATALOGUE = [
  { id: 'a', code: 'headache', name_en: 'Headache', name_bn: 'মাথাব্যথা',
    synonyms_en: ['head pain'], synonyms_bn: [], status: 'active', sort_order: 10 },
  { id: 'b', code: 'cough', name_en: 'Cough', name_bn: 'কাশি',
    synonyms_en: [], synonyms_bn: [], status: 'active', sort_order: 20 },
  { id: 'c', code: 'dizziness', name_en: 'Dizziness', name_bn: 'মাথা ঘোরা',
    synonyms_en: [], synonyms_bn: [], status: 'active', sort_order: 30 },
];
const index = createCatalogueIndex(CATALOGUE);

test('a booking starts with nothing recorded', () => {
  const empty = emptySelection();
  assert.deepEqual(empty, { ids: [], texts: [] });
  assert.equal(countOf(empty), 0);
  assert.equal(hasRoom(empty), true);
  assert.deepEqual(toPayload(empty), { symptom_ids: [], symptom_texts: [] });
});

test('catalogue entries are added once, in the order they were chosen', () => {
  const first = addCatalogue(emptySelection(), { id: 'b' });
  assert.equal(first.changed, true);
  assert.equal(first.reason, 'added');
  const second = addCatalogue(first.selection, { id: 'a' });
  assert.deepEqual(second.selection.ids, ['b', 'a']);
  assert.equal(isSelected(second.selection, 'a'), true);
});

test('adding the same catalogue entry twice changes nothing', () => {
  const once = addCatalogue(emptySelection(), { id: 'a' }).selection;
  const twice = addCatalogue(once, { id: 'a' });
  assert.equal(twice.changed, false);
  assert.equal(twice.reason, 'duplicate');
  assert.deepEqual(twice.selection.ids, ['a']);
});

test('free text is stored collapsed so the chip and the record agree', () => {
  const result = addFreeText(emptySelection(), '  মাথা   ব্যথা  ');
  assert.equal(result.changed, true);
  assert.equal(result.text, 'মাথা ব্যথা');
  assert.deepEqual(result.selection.texts, ['মাথা ব্যথা']);
});

test('the same free-text description cannot be added twice', () => {
  const once = addFreeText(emptySelection(), 'মাথা ব্যথা').selection;
  assert.equal(addFreeText(once, 'মাথা   ব্যথা').reason, 'duplicate');
  assert.equal(addFreeText(once, 'মাথা ব্যথা ').reason, 'duplicate');
});

test('empty and over-long descriptions are refused', () => {
  assert.equal(addFreeText(emptySelection(), '   ').reason, 'empty');
  assert.equal(addFreeText(emptySelection(), 'ক'.repeat(201)).reason, 'too-long');
  assert.equal(addFreeText(emptySelection(), 'ক'.repeat(200)).changed, true);
});

test('the cap is enforced for both kinds', () => {
  let selection = emptySelection();
  for (let i = 0; i < 3; i += 1) {
    selection = addFreeText(selection, `complaint ${i}`, { max: 3 }).selection;
  }
  const overflow = addFreeText(selection, 'one too many', { max: 3 });
  assert.equal(overflow.changed, false);
  assert.equal(overflow.reason, 'full');
  assert.equal(countOf(selection), 3);
  assert.equal(addCatalogue(selection, { id: 'a' }, { max: 3 }).reason, 'full');
});

test('a chip can be removed by kind', () => {
  let selection = addCatalogue(emptySelection(), { id: 'a' }).selection;
  selection = addFreeText(selection, 'বিশেষ কিছু').selection;
  selection = addCatalogue(selection, { id: 'b' }).selection;
  const withoutCatalogue = removeChip(selection, { kind: 'catalogue', id: 'a' });
  assert.deepEqual(withoutCatalogue.ids, ['b']);
  assert.deepEqual(withoutCatalogue.texts, ['বিশেষ কিছু']);
  const withoutText = removeChip(withoutCatalogue, { kind: 'free_text', text: 'বিশেষ কিছু' });
  assert.deepEqual(withoutText.texts, []);
});

test('comma/Tab adds only an unambiguous entry and leaves ambiguity alone', () => {
  const ok = commitFromQuery(index, 'মাথাব্যথা', emptySelection());
  assert.equal(ok.changed, true);
  assert.deepEqual(ok.selection.ids, ['a']);
  const ambiguous = commitFromQuery(index, 'মাথা', emptySelection());
  assert.equal(ambiguous.changed, false);
  assert.equal(ambiguous.reason, 'ambiguous');
  assert.deepEqual(ambiguous.selection.ids, []);
  const nothing = commitFromQuery(index, 'zzz', emptySelection());
  assert.equal(nothing.changed, false);
  assert.equal(nothing.reason, 'none');
});

test('comma/Tab does not re-add an entry that is already selected', () => {
  const selection = addCatalogue(emptySelection(), { id: 'a' }).selection;
  const again = commitFromQuery(index, 'মাথাব্যথা', selection);
  assert.equal(again.changed, false);
  assert.deepEqual(again.selection.ids, ['a']);
});

test('chips keep the catalogue/free-text distinction and stable keys', () => {
  let selection = addCatalogue(emptySelection(), { id: 'a' }).selection;
  selection = addFreeText(selection, 'বিশেষ কিছু').selection;
  const chips = chipsOf(selection, index);
  assert.deepEqual(chips[0], {
    kind: 'catalogue', id: 'a', name_en: 'Headache', name_bn: 'মাথাব্যথা',
  });
  assert.deepEqual(chips[1], { kind: 'free_text', text: 'বিশেষ কিছু' });
  assert.equal(chipKey(chips[0]), 'cat:a');
  assert.equal(chipKey(chips[1]), 'txt:বিশেষ কিছু');
});

test('the payload keeps the two lists apart', () => {
  let selection = addCatalogue(emptySelection(), { id: 'b' }).selection;
  selection = addFreeText(selection, 'হঠাৎ শুরু').selection;
  assert.deepEqual(toPayload(selection), {
    symptom_ids: ['b'], symptom_texts: ['হঠাৎ শুরু'],
  });
});

test('the default cap matches the server', () => {
  assert.equal(DEFAULT_MAX_SYMPTOMS, 20);
});
