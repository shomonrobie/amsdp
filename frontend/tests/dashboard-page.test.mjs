/* MP-22 — dashboard completion, asserted against the page source.
 *
 * The page is JSX and this repository ships no DOM renderer (see the note in
 * `dashboard-tiles.test.mjs`), so what is proved here is the *contract* of the
 * screen: both selectors exist and are wired to the server-side query builders,
 * the two panel endpoints are the ones actually called, the facility day is the
 * server's answer rather than something the browser invents, and every label the
 * page asks for exists in **both** languages.
 *
 * `dashboard-tiles.test.mjs` keeps its MP-07 promise independently: this rewrite
 * did not touch the six `{ label: t('…'), value: today.<field> || 0 }` entries.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { tIn } from '../lib/i18n.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const PAGE = fs.readFileSync(path.join(FE, 'pages', 'dashboard.js'), 'utf8');
const POLICY = fs.readFileSync(path.join(FE, 'lib', 'dashboard.js'), 'utf8');

test('the page owns no server-side data, so it prerenders like its neighbours', () => {
  assert.ok(!/getServerSideProps/.test(PAGE),
    'MP-22: the leftover getServerSideProps stub must stay gone');
});

test('the branch selector is populated from the shared authorisation rule', () => {
  assert.match(PAGE, /selectableBranches\(rows, user\)/,
    'the selector must filter through lib/dashboard.js, not list every branch');
  assert.match(PAGE, /<select[^>]*value=\{branchId\}/);
  assert.match(PAGE, /\/api\/v1\/orgs\/.*\/branches/);
});

test('the date selector is a real date input, sent through the query builder', () => {
  assert.match(PAGE, /<input type="date"[^>]*value=\{date\}/);
  assert.match(PAGE, /dashboardQuery\(\{ branchId, date \}\)/,
    'the day must travel to the server, not be filtered in the browser');
});

test('the page calls the two dashboard endpoints and nothing else panel-shaped', () => {
  assert.match(PAGE, /\/api\/v1\/dashboard\/today/);
  assert.match(PAGE, /\/api\/v1\/dashboard\/audit/);
  assert.match(PAGE, /activityQuery\(\{ branchId, limit: 8 \}\)/);
});

test('the facility day is displayed from the server response, never computed here', () => {
  assert.match(PAGE, /today\.facility_today/);
  assert.ok(!/toISOString\(\)/.test(PAGE),
    'a browser-computed date would disagree with the facility calendar (BR §8)');
});

test('the queue panel renders the per-doctor breakdown through the shared rule', () => {
  assert.match(PAGE, /perDoctorRows\(today\)/);
  assert.match(PAGE, /today\.queue_length/);
});

test('quick actions come from the role rule rather than a hard-coded list', () => {
  assert.match(PAGE, /quickActionsFor\(user\)/);
  assert.ok(!/href="\/appointments\/new"/.test(PAGE),
    'the shortcut list must not be duplicated inline in the page');
});

test('the recent-activity panel labels known actions and shows unknown ones as themselves', () => {
  assert.match(PAGE, /row\.labelKey \? t\(row\.labelKey\) : row\.action/);
});

test('every label the page asks for exists in both languages', () => {
  const keys = new Set();
  const re = /\bt\('([A-Za-z0-9_]+)'\)/g;
  let m;
  while ((m = re.exec(PAGE)) !== null) keys.add(m[1]);
  assert.ok(keys.size > 10, 'expected the page to use a vocabulary, found ' + keys.size);
  const missing = [];
  for (const key of keys) {
    if (tIn('bn', key) === key) missing.push('bn:' + key);
    if (tIn('en', key) === key) missing.push('en:' + key);
  }
  assert.deepEqual(missing, [], 'missing translations: ' + missing.join(', '));
});

test('the policy module states that it is not an authorization boundary', () => {
  assert.match(POLICY, /None of it is an authorization boundary/i);
  assert.match(POLICY, /non-disclosing 404/i);
});
