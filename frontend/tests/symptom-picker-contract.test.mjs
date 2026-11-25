/* Symptom picker — source-level contract.
 *
 * AMSDP-SYMPTOM-01.  Node's test runner here has no DOM harness (the jsdom
 * attempt is recorded as abandoned for memory reasons in
 * AMSDP_Frontend_Usability_Shared_Design_System_and_Demo_Readiness_V1.0.md §9),
 * so the component's *rules* are covered by the two pure-module suites
 * (`symptom-catalogue-matcher`, `symptom-catalogue-selection`) and the
 * component's *structure* is pinned here.  What this file can prove, and what
 * it deliberately does not claim:
 *
 *   proved     — the picker owns no effect (so it cannot re-introduce the
 *                focus-loss defect class), it reuses the BanglaNameSense
 *                normaliser instead of forking the language sense, the booking
 *                page sends the symptom fields, the page passes no patient age
 *                or sex into the picker, the catalogue is not hard-coded in the
 *                UI, and every new caption exists in both languages;
 *   not proved — that typing works in a browser.  No browser run was performed
 *                for this feature (see the implementation report's status table).
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DICT } from '../lib/i18n.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const read = (rel) => fs.readFileSync(path.join(FE, rel), 'utf8');

const PICKER = 'components/SymptomPicker.js';
const PAGE = 'pages/appointments.js';
const MATCHER = 'lib/symptom-catalogue/matcher.js';

/** Code only — comments are where the examples live, not where the rules do. */
const stripComments = (source) =>
  source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

/** Everything between `<Name` and the closing `/>` of a JSX element. */
function jsxProps(source, name) {
  const start = source.indexOf('<' + name);
  if (start === -1) return '';
  const end = source.indexOf('/>', start);
  return end === -1 ? source.slice(start) : source.slice(start, end);
}

test('the picker owns no effect, so focus can never be stolen mid-typing', () => {
  const source = read(PICKER);
  assert.doesNotMatch(source, /useEffect|useLayoutEffect/,
    'SymptomPicker must own no effect at all — an effect keyed on a callback prop '
    + 'is the AMSDP-FRONTEND-UX-DEMO-01 focus-loss defect');
  // The only focus call is the handler that returns the caret after a chip act.
  assert.match(source, /const focusInput = \(\) => \{/,
    'focus is a named handler, not an effect');
});

test('the picker reuses the BanglaNameSense language sense', () => {
  const matcher = stripComments(read(MATCHER));
  assert.match(matcher, /from '\.\.\/bangla-name-sense\/normalize\.js'/,
    'normalisation must be imported from the shipped BanglaNameSense module');
  for (const helper of ['normalizeBangla', 'normalizeLatin', 'wordsOf',
    'matchesWordPrefixesInOrder']) {
    assert.match(matcher, new RegExp(`\\b${helper}\\b`), `reuses ${helper}`);
  }
  assert.doesNotMatch(matcher, /bangla-name-sense\/(matcher|controller)\.js/,
    'the name-specific matcher/controller must not be forked into the symptom path');
});

test('the catalogue is never hard-coded in the UI', () => {
  const page = stripComments(read(PAGE));
  const picker = stripComments(read(PICKER));
  /* Letter-bounded, not a bare substring: `প্রকাশিত` ("published") contains the
     letters of `কাশি` ("cough") without being that word, and flags the Bangla
     copy that explains published hours.  Bangla joins words with a virama or a
     space, so the boundary is "not another letter". */
  const mentions = (text, name) =>
    new RegExp('(?<!\\p{L})' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?!\\p{L})', 'u')
      .test(text);
  for (const name of ['মাথাব্যথা', 'Chest pain', 'কাশি', 'জ্বর', 'headache']) {
    assert.ok(!mentions(page, name), `a symptom name leaked into the page: ${name}`);
    assert.ok(!mentions(picker, name), `a symptom name leaked into the picker: ${name}`);
  }
  assert.match(page, /apiFetch\('\/api\/v1\/symptoms'\)/,
    'the catalogue comes from the API');
});

test('the booking form posts the symptom fields, optional and empty by default', () => {
  const page = read(PAGE);
  for (const field of ['symptom_ids', 'symptom_texts', 'symptom_onset',
    'symptom_onset_note']) {
    assert.ok(page.includes(`${field}:`), `booking payload must carry ${field}`);
  }
  // The booking dialog and the walk-in dialog both start from an empty selection.
  assert.equal((page.match(/symptoms: \{ ids: \[\], texts: \[\] \}/g) || []).length, 2,
    'both booking dialogs initialise an empty symptom selection');
});

test('the page never gives the picker the patient age or sex', () => {
  const page = read(PAGE);
  for (const element of ['SymptomPicker', 'OnsetField']) {
    const props = jsxProps(page, element);
    assert.ok(props, `${element} is rendered`);
    assert.doesNotMatch(props, /\b(age|sex|dob|gender|patient)\b/,
      `${element} must not receive patient demographics: age and sex may never `
      + 'influence which symptom is offered');
  }
  // The selected doctor's speciality is the only context passed.
  assert.match(jsxProps(page, 'SymptomPicker'), /contextSpecialtyCodes=/);
});

test('the receptionist sees the recorded symptoms on the appointment', () => {
  const page = read(PAGE);
  assert.match(page, /\[t\('aptSy'\), symptomLine\(detail\)\]/);
  assert.match(page, /\[t\('aptOnset'\), onsetLine\(detail\)\]/);
  assert.ok(page.includes('s.kind === \'catalogue\''),
    'the detail view keeps catalogue entries and free text apart');
});

test('every new caption exists in both languages', () => {
  // MP-28 moved these keys out of the page's own table into lib/i18n.js, so
  // the assertion is made against the dictionary itself rather than the source.
  const keys = ['aptSy', 'aptSyNone', 'aptOnset', 'aptSyPrompt', 'aptSyPlaceholder',
    'aptSyOptional', 'aptSySelected', 'aptSyRemove', 'aptSyFreeText', 'aptSyAddFree',
    'aptSyAlready', 'aptSyFull', 'aptSyHint', 'aptSyList', 'aptOnsetPrompt',
    'aptOnsetNotAsked', 'aptOnsetNote', 'aptOnsetNotePlaceholder'];
  for (const key of keys) {
    assert.ok(DICT.bn[key] && DICT.bn[key].trim(), `${key} must be defined in Bangla`);
    assert.ok(DICT.en[key] && DICT.en[key].trim(), `${key} must be defined in English`);
  }
});

test('the picker labels come from the shared dictionary', () => {
  const page = read(PAGE);
  for (const mapped of ['title: t(\'aptSy\')', 'prompt: t(\'aptSyPrompt\')',
    'onsetTitle: t(\'aptOnsetPrompt\')', 'addFree: t(\'aptSyAddFree\')']) {
    assert.ok(page.includes(mapped), `labels must be wired: ${mapped}`);
  }
});
