/* MP-28 — one i18n mechanism, asserted rather than described.
 *
 * Before this task the frontend translated strings three ways: `lib/i18n.js`
 * (the shared DICT), a page-local `const L = { bn: {...}, en: {...} }` plus a
 * local `T()` helper in five screens, and component-local Bangla-only label
 * defaults. The five page dictionaries were moved into `lib/i18n.js`
 * verbatim, so this file guards the result:
 *
 *   1. both languages carry exactly the same keys, with no silent fallbacks;
 *   2. no page-local dictionary or translator has come back;
 *   3. every literal key a page asks for exists in Bangla *and* English;
 *   4. the keys built at runtime (server refusals, appointment types) resolve
 *      too, because those are the ones a coverage test usually misses.
 *
 * The test fails when a key is missing, which is MP-28's acceptance criterion.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DICT, t } from '../lib/i18n.js';
import {
  REFUSAL_KEYS, APPOINTMENT_TYPES, typeLabelKey, typeBadgeKey,
} from '../lib/calendar/booking.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const I18N_SRC = fs.readFileSync(path.join(FE, 'lib', 'i18n.js'), 'utf8');
const PAGES = fs.readdirSync(path.join(FE, 'pages')).filter((f) => f.endsWith('.js'));
const COMPONENTS = fs.readdirSync(path.join(FE, 'components'))
  .filter((f) => f.endsWith('.js'));

const bnKeys = Object.keys(DICT.bn);
const enKeys = Object.keys(DICT.en);

/** The keys a file asks for through the shared helper, literal arguments only. */
function requestedKeys(source) {
  const keys = new Set();
  for (const m of source.matchAll(/(?<![\w$.])t\(\s*'([A-Za-z0-9_$]+)'/g)) {
    keys.add(m[1]);
  }
  for (const m of source.matchAll(/tIn\(\s*'[a-z]{2}'\s*,\s*'([A-Za-z0-9_$]+)'/g)) {
    keys.add(m[1]);
  }
  return keys;
}

const aptKey = (k) => 'apt' + String(k).charAt(0).toUpperCase() + String(k).slice(1);

test('Bangla and English carry exactly the same keys', () => {
  const missingEn = bnKeys.filter((k) => !enKeys.includes(k));
  const missingBn = enKeys.filter((k) => !bnKeys.includes(k));
  assert.deepEqual(missingEn, [], `keys with no English string: ${missingEn}`);
  assert.deepEqual(missingBn, [], `keys with no Bangla string: ${missingBn}`);
  assert.ok(bnKeys.length > 400,
    `expected the whole dictionary, found ${bnKeys.length} keys`);
});

test('no key resolves to itself, an empty string or a non-string', () => {
  for (const lang of ['bn', 'en']) {
    for (const [key, value] of Object.entries(DICT[lang])) {
      assert.equal(typeof value, 'string', `${lang}.${key} is not a string`);
      assert.ok(value.trim().length > 0, `${lang}.${key} is empty`);
      if (lang === 'bn') {
        // a Bangla string can never be the Latin key: that is the silent-fallback smell
        assert.notEqual(value, key, `bn.${key} would fall back to its own key`);
      }
    }
  }
});

test('the dictionary source declares no duplicate key in either language', () => {
  const block = (start, end) => I18N_SRC.slice(
    I18N_SRC.indexOf(start), I18N_SRC.indexOf(end));
  const pairs = [['  bn: {', '  en: {'], ['  en: {', '\n};']];
  for (const [start, end] of pairs) {
    const body = block(start, end);
    const declared = [...body.matchAll(/^\s{4}([A-Za-z_$][\w$]*)\s*:/gm)]
      .map((m) => m[1]);
    const dupes = declared.filter((k, i) => declared.indexOf(k) !== i);
    assert.deepEqual([...new Set(dupes)], [],
      `duplicate keys in the ${start.trim()} block`);
    assert.ok(declared.length > 200, `parsed only ${declared.length} keys`);
  }
});

test('no page keeps a local {bn,en} dictionary or its own translator', () => {
  const offenders = [];
  for (const file of PAGES.concat(COMPONENTS.map((f) => '../components/' + f))) {
    const full = file.startsWith('../')
      ? path.join(FE, 'components', path.basename(file))
      : path.join(FE, 'pages', file);
    const src = fs.readFileSync(full, 'utf8');
    if (/const\s+L\s*=\s*\{[^}]{0,80}\bbn\s*:\s*\{/s.test(src) ||
        /function\s+T\s*\(\s*[A-Za-z_$][\w$]*\s*\)\s*\{/.test(src) ||
        /const\s+L\s*=\s*\{\s*bn:/.test(src)) {
      offenders.push(path.relative(FE, full));
    }
  }
  assert.deepEqual(offenders, [],
    `these files still translate on their own: ${offenders.join(', ')}`);
});

test('every literal key a page asks for exists in Bangla and English', () => {
  let checked = 0;
  const missing = [];
  for (const file of PAGES) {
    const src = fs.readFileSync(path.join(FE, 'pages', file), 'utf8');
    for (const key of requestedKeys(src)) {
      checked += 1;
      if (!(key in DICT.bn) || !(key in DICT.en)) missing.push(`${file}: ${key}`);
    }
  }
  assert.deepEqual(missing, [], `unknown keys: ${missing.join(', ')}`);
  assert.ok(checked > 250,
    `the scan only found ${checked} key references — it is not reading the pages`);
});

test('keys built at runtime resolve through the same dictionary', () => {
  const missing = [];
  for (const key of Object.values(REFUSAL_KEYS)) {
    if (!(aptKey(key) in DICT.bn)) missing.push(aptKey(key));
  }
  for (const type of APPOINTMENT_TYPES) {
    for (const built of [typeLabelKey(type), typeBadgeKey(type)]) {
      if (!built) continue;      // `scheduled` deliberately carries no badge
      if (!(aptKey(built) in DICT.bn)) missing.push(aptKey(built));
    }
  }
  assert.deepEqual(missing, [], `runtime keys with no string: ${missing.join(', ')}`);
});

test('an unknown key returns itself instead of throwing', () => {
  assert.equal(t('mp28.key.that.does.not.exist'), 'mp28.key.that.does.not.exist');
});
