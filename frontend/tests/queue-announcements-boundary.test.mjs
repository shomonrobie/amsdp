/* QUE-006 / OD-1 — the queue-page boundary.
 *
 * The unit tests above prove the mechanism. This file proves the *wiring*: the
 * panel and the queue page parse as JSX, every caption is bilingual, the
 * announcement never becomes a queue write, and the panel does not render
 * browser-only state on the server (the queue page is server-rendered).
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DICT } from '../lib/i18n.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const BOUNDARY = ['pages/queue.js', 'components/queue/QueueAnnouncements.js'];

const read = (rel) => fs.readFileSync(path.join(FE, rel), 'utf8');

let swc = null;
try {
  swc = (await import(FE + '/node_modules/next/dist/build/swc/index.js')).default;
} catch {
  swc = null;
}

test('the queue page and the announcement panel compile as JSX', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  for (const rel of BOUNDARY) {
    const out = await swc.transform(read(rel), {
      filename: path.basename(rel),
      jsc: {
        parser: { syntax: 'ecmascript', jsx: true },
        transform: { react: { runtime: 'classic', development: false } },
      },
      module: { type: 'es6' },
    });
    assert.ok(out.code.length > 500, `${rel} compiled to something substantial`);
  }
});

test('every caption the announcement boundary asks for is bilingual', () => {
  const used = new Set();
  BOUNDARY.forEach((rel) => {
    for (const m of read(rel).matchAll(/t\('([A-Za-z0-9_]+)'\)/g)) used.add(m[1]);
  });
  assert.ok(used.size >= 8, 'the boundary does ask for localised text');
  const missing = [...used].filter((key) => !(key in DICT.bn) || !(key in DICT.en));
  assert.deepEqual(missing, [], `missing dictionary keys: ${missing.join(', ')}`);
  used.forEach((key) => {
    assert.ok(String(DICT.bn[key]).trim().length > 0, `bn.${key} is empty`);
    assert.ok(String(DICT.en[key]).trim().length > 0, `en.${key} is empty`);
  });
});

test('the queue page owns one announcer and renders the panel', () => {
  const src = read('pages/queue.js');
  assert.match(src, /useQueueAnnouncements/);
  assert.match(src, /<QueueAnnouncements controller=\{announcements\}/);
  assert.match(src, /r\.status === 'called'/,
    'the audible announcement is offered for a called entry');
});

test('announcing is not a queue action', () => {
  const page = read('pages/queue.js');
  const start = page.indexOf('const announceEntry');
  assert.ok(start > 0, 'announceEntry exists');
  const body = page.slice(start, page.indexOf('\n  };', start));
  // No API call, no queue transition: audio never writes queue state.
  assert.ok(!/apiFetch/.test(body), 'announcing must not call the API');
  assert.ok(!/queue\/'/.test(body), 'announcing must not PATCH a queue entry');
  assert.match(body, /source: 'operator'/, 'a manual repeat is marked as operator intent');
  assert.match(body, /userGesture: true/, 'a click may recover audio the browser blocked');
});

test('the page announces the room the payload carries', () => {
  const page = read('pages/queue.js');
  const start = page.indexOf('const announceEntry');
  const body = page.slice(start, page.indexOf('\n  };', start));
  // QUE-006 / F4: the room reaches the announcement from the queue payload's
  // appointment snapshot (`room_name`), never from a placeholder field.
  assert.match(body, /room: entry\.room_name/,
    'the announcement reads the room the payload carries');
  assert.ok(!/room: entry\.room,/.test(body),
    'the stale `entry.room` placeholder is gone');
});

test('the panel defers browser state until after mount', () => {
  const src = read('components/queue/QueueAnnouncements.js');
  assert.match(src, /if \(!mounted\) return null;/,
    'the server cannot know the voice list, so nothing is rendered before mount');
  // No foreign-domain decision is taken in the view.
  assert.ok(!/speechSynthesis\.speak/.test(src), 'the panel never talks to the engine directly');
});
