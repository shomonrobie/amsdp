/* MP-38 / MP-42 / MP-43 / MP-45 / MP-28 — the public display board.
 *
 * This project ships no DOM renderer, so the page is asserted against its source
 * (the same convention `staff-page.test.mjs` uses) and against the **server it
 * talks to**: a field the page renders must exist in the payload the route
 * builds, and a field the facility switched off must be absent from that payload
 * rather than hidden here.
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
const REPO = path.resolve(FE, '..');

const PAGE = fs.readFileSync(
  path.join(FE, 'pages', 'queue-display', '[org]', '[branch].js'), 'utf8');
const API = fs.readFileSync(
  path.join(REPO, 'backend', 'queuing', 'display.py'), 'utf8');
const CSS = fs.readFileSync(path.join(FE, 'styles', 'global.css'), 'utf8');

test('MP-28 — the board no longer carries its own dictionary', () => {
  const has = (re, src, msg) => assert.ok(re.test(src), msg);
  assert.ok(!/const\s+L\s*=\{/.test(PAGE), 'no page-local {bn,en} table');
  assert.ok(!/function\s+T\s*\(\s*k\s*\)/.test(PAGE), 'no page-local translator');
  has(/from '\.\.\/\.\.\/\.\.\/lib\/i18n'/, PAGE, 'the shared dictionary is imported');
  has(/const tr=\(k\)=>tIn\(lang,k\);/, PAGE, 'translation goes through the shared helper');
  has(/tIn\(lang,\s*k\)/, PAGE, 'tIn is the only mechanism');
});

test('MP-38 — the configured language sits below ?lang= and above the device', () => {
  const has = (re, src, msg) => assert.ok(re.test(src), msg);
  has(/lang=\(bn\|en\)/, PAGE, 'the ?lang= override is read');
  has(/d\.display&&d\.display\.language/, PAGE, 'the configured language decides');
  has(/if\(!wanted\|\|langLocked\|\|wanted===configuredLang\) return;/,
    PAGE, 'a locked override must not be overwritten by a poll');
  has(/const configured=!!\(d&&d\.display&&d\.display\.language\);/, PAGE,
    'the toggle knows whether it overrides a configured board');
  has(/history\.replaceState/, PAGE, 'the override is written into the URL');
  has(/localStorage\.getItem/, PAGE, 'a device preference exists for unconfigured boards');
  // The device preference is consulted only where a display is not configured:
  // deviceLang() is called from the mount effect, never from the payload effect.
  const payloadEffect = PAGE.slice(PAGE.indexOf('const wanted='),
    PAGE.indexOf('React.useEffect', PAGE.indexOf('const wanted=')));
  assert.ok(payloadEffect.indexOf('deviceLang') < 0,
    'a configured board never falls back to storage');
});


test('MP-43 — the page revalidates and a 304 changes no state', () => {
  const has = (re, src, msg) => assert.ok(re.test(src), msg);
  has(/If-None-Match/, PAGE, 'the board revalidates');
  has(/r\.status===304/, PAGE, 'a 304 is handled');
  has(/r\.headers\.get\('ETag'\)/, PAGE, 'the weak validator is kept');
  const branch = PAGE.slice(PAGE.indexOf('r.status===304'), PAGE.indexOf('if(r.status===404)'));
  assert.ok(!/setD\(|setPhase\(|setLastUpd\(/.test(branch),
    'an unchanged board must not re-render');
  has(/board_version/, API, 'the route publishes a version');
  has(/status_code=304/, API, 'and answers 304');
});

test('MP-45 / MD-17 — a switched-off field is absent from the payload', () => {
  for (const field of ['show_room', 'show_estimated_wait', 'show_waiting_count']) {
    assert.ok(API.indexOf('display.' + field) >= 0, 'the route must read ' + field);
  }
  assert.ok(/if show_room:/.test(API), 'the room field is conditional');
  assert.ok(/if show_wait:/.test(API), 'the estimate is conditional');
  assert.ok(/if show_count:/.test(API), 'the count is conditional');
  // The page renders only what is present, so absence is honest.
  assert.ok(PAGE.indexOf('doc.room_name!==undefined') >= 0);
  assert.ok(PAGE.indexOf('doc.patients_waiting!==undefined') >= 0);
  assert.ok(PAGE.indexOf('doc.estimated_wait_minutes!==undefined') >= 0);
});

test('MP-42 — the estimate is always marked as an estimate', () => {
  assert.ok(PAGE.indexOf('dqds-est-badge') >= 0, 'the marker renders beside the number');
  assert.ok(PAGE.indexOf('dqdsEstWait') >= 0, 'and is labelled in the board language');
  assert.ok(API.indexOf('row["estimate"] = True') >= 0, 'the payload carries the flag');
  assert.ok(API.indexOf('max(1, math.ceil(sample))') >= 0, 'a measured mean is floored at 1');
  assert.ok(API.indexOf('else default_minutes') >= 0, 'a doctor without samples gets the default');
});

test('MP-37 — the room label renders a dash, never an invented room', () => {
  assert.ok(/doc\.room_name\|\|DASH/.test(PAGE));
  assert.ok(API.indexOf('row["room_name"] = rooms.get(doc_id)') >= 0);
});

test('MP-38 / AC-11 — the token is the largest element by construction', () => {
  const block = CSS.slice(CSS.indexOf('.dqds-token'), CSS.indexOf('.dqds-wait-count'));
  assert.ok(/font-size:clamp\(/.test(block), 'the type scale is viewport-relative');
  const token = block.match(/font-size:clamp\(([\d.]+)rem,\s*([\d.]+)vw/);
  assert.ok(token, 'the token must declare a clamp()');
  assert.ok(Number(token[1]) >= 1.8, 'the token floor is at least 1.8rem');
  assert.ok(CSS.indexOf('max-width:1180px') < 0, 'the old fixed card cap is gone');
  assert.ok(/\.dqds-card[^}]*max-width:min\(96vw,1800px\)/.test(CSS));
});

test('MP-38 — the scope label is translated by the board, not by a free variable', () => {
  // Regression: `scopeLabel` lives at module scope, so it has no access to the
  // component's `tr`.  An earlier call site passed an undefined `T` while the
  // helper referenced the component-scope `tr`, which threw a ReferenceError the
  // moment a non-branch display rendered — the seeded "cardio" department board
  // is exactly such a display, so the crash would have hit the demonstration.
  assert.ok(/scopeLabel\(display,tr\)/.test(PAGE),
    'the call site passes the translator the board is using');
  const helper = PAGE.slice(PAGE.indexOf('function scopeLabel'));
  assert.ok(/^function scopeLabel\(display,tr\)\{/.test(helper),
    'the helper declares its translator as a parameter');
  assert.ok(!/\bT\b/.test(helper.slice(0, helper.indexOf('\n}'))),
    'no undefined placeholder identifier survives in the helper');
  // Every scope type renders a label, and each one is a translated key.
  for (const key of ['dispScopeBranch', 'dispScopeDoctors',
    'dispScopeDepartment', 'dispScopeRoom']) {
    assert.ok(helper.indexOf("tr('" + key + "')") >= 0, key + ' is rendered');
  }
  const scope = PAGE.slice(PAGE.indexOf('data-testid="dqds-scope"'));
  assert.ok(scope.indexOf('dispScope') >= 0, 'the scope is labelled in the board language');
});

test('every string the board asks for exists in both languages', () => {
  const keys = new Set();
  for (const m of PAGE.matchAll(/\btr\('([A-Za-z0-9_$]+)'\)/g)) keys.add(m[1]);
  assert.ok(keys.size >= 15, 'the board is expected to be fully translated');
  const missing = [];
  for (const locale of ['bn', 'en']) {
    for (const key of keys) {
      if (DICT[locale][key] === undefined) missing.push(locale + '.' + key);
    }
  }
  assert.deepEqual(missing, [], 'untranslated board strings');
});

test('the board stays public, read-only and PII-free', () => {
  assert.ok(PAGE.indexOf('Authorization') < 0, 'no credential is sent by a public board');
  assert.ok(PAGE.indexOf('patient_name') < 0 && PAGE.indexOf('patient_id') < 0,
    'no patient identity reaches the screen');
  assert.ok(API.indexOf('methods=["POST", "PUT", "PATCH", "DELETE"]') >= 0,
    'the write verbs are guarded');
  assert.ok(API.indexOf('"Allow": "GET"') >= 0, 'and answered with Allow: GET');
});

