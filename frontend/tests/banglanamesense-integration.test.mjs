/* BanglaNameSense — AMSDP integration and regression-preservation tests.
 *
 * The React component is JSX, which plain Node cannot parse without a bundler,
 * and the project deliberately has no DOM/component-test dependency. These
 * tests therefore pin the *contract* between the page, the component and the
 * pure engine, and prove that no existing patient-registration behaviour was
 * changed. They are complemented by `npm run build` (the component must compile
 * in the real Next pipeline) and by the backend patient suite.
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const read = (rel) => readFileSync(new URL(rel, import.meta.url), 'utf8');
const page = read('../pages/patients.js');
const component = read('../components/BanglaNameSense.js');
const matcher = read('../lib/bangla-name-sense/matcher.js');
const controller = read('../lib/bangla-name-sense/controller.js');

test('patient registration page uses the reusable BanglaNameSense component', () => {
  assert.match(page, /import BanglaNameSense from '\.\.\/components\/BanglaNameSense'/);
  assert.match(page, /<div className='form-group'><BanglaNameSense id='patient-name'/);
  assert.match(page, /value=\{f\.name\}/);
  assert.match(page, /onChange=\{v=>setF\(\{\.\.\.f,name:v\}\)\}/);
  assert.match(page, /label=\{t\('patN'\)\}/);
  assert.match(page, /required/);
});

test('the name field is still mandatory and still labelled', () => {
  assert.match(component, /label &&/, 'label must be rendered when provided');
  assert.match(component, /\{required \? '\*' : ''\}/, 'asterisk contract kept');
  assert.match(component, /aria-required=\{required \|\| undefined\}/);
});

test('existing patient registration behaviour is preserved verbatim', () => {
  // API contract, payload shape, duplicate warning and search are untouched.
  assert.match(page, /const payload=\{\.\.\.f\};/);
  assert.match(page, /delete payload\.date_of_birth/);
  assert.match(page, /delete payload\.age/);
  assert.match(page, /fetch\('\/api\/v1\/patients',\{method:'POST'/);
  assert.match(page, /setDupes\(d\.duplicates\|\|\[\]\)/);
  assert.match(page, /t\('patDup'\)/);
  assert.match(page, /fetch\('\/api\/v1\/patients\?q='/);
  // Role gating on the Register button is unchanged.
  assert.match(page, /u\.role==='receptionist'/);
  assert.match(page, /if\(!u\.id\)return null;/);
  // No patient record is created from a suggestion.
  assert.equal((page.match(/method:'POST'/g) || []).length, 1);
});

test('the component is accessible as a combobox with a listbox of options', () => {
  assert.match(component, /role="combobox"/);
  assert.match(component, /aria-autocomplete="list"/);
  assert.match(component, /aria-expanded=\{open\}/);
  assert.match(component, /aria-controls=\{listId\}/);
  assert.match(component, /aria-activedescendant=\{activeId\}/);
  assert.match(component, /role="listbox"/);
  assert.match(component, /role="option"/);
  assert.match(component, /aria-selected=\{i === state\.activeIndex\}/);
  assert.match(component, /aria-live="polite"/);
});

test('keyboard, mouse and touch input are all wired', () => {
  assert.match(component, /onKeyDown=\{handleKeyDown\}/);
  assert.match(component, /onBlur=\{handleBlur\}/);
  assert.match(component, /onFocus=\{handleFocus\}/);
  assert.match(component, /onMouseDown=\{\(e\) => \{ e\.preventDefault\(\); pick\(i\); \}\}/);
  assert.match(component, /onTouchStart=\{\(e\) => \{ e\.preventDefault\(\); pick\(i\); \}\}/);
  // Key handling is delegated to the tested pure reducer, not re-implemented.
  assert.match(component, /keyDown\(state, event\.key\)/);
});

test('the suggestion path is local — no network, no AI service', () => {
  assert.doesNotMatch(component, /fetch\s*\(/);
  assert.doesNotMatch(component, /XMLHttpRequest/);
  assert.doesNotMatch(component, /\/api\//);
  assert.doesNotMatch(matcher, /fetch\s*\(/);
  assert.doesNotMatch(controller, /fetch\s*\(/);
});

test('gender metadata is never used for filtering, ranking or display', () => {
  assert.doesNotMatch(component, /gender/i);
  assert.doesNotMatch(matcher, /gender/i);
  assert.doesNotMatch(controller, /gender/i);
  assert.doesNotMatch(page, /gender/i);
});

test('the component never rewrites the input on its own', () => {
  // The only paths that change the field are the user typing and an explicit pick.
  const changeCalls = component.match(/onChange\(([^)]*)\)/g) || [];
  assert.ok(changeCalls.every((c) => /onChange\((text|result\.value)\)/.test(c)),
    `unexpected onChange call: ${changeCalls.join(', ')}`);
  assert.match(component, /onChange=\{\(e\) => applyText\(e\.target\.value\)\}/);
});
