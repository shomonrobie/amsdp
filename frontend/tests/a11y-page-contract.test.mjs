/* MP-29 — the screen-level half of the accessibility pass, asserted from source.
 *
 * `a11y.test.mjs` proves the decisions; this file proves the *sheet* and the
 * *markup* follow them, because a correct helper nobody calls fixes nothing:
 *
 *   1. every `:hover` in `global.css` has a `:focus-visible`/`:focus-within` twin;
 *   2. no rule hides a control until it is hovered;
 *   3. the 44 px target floor and the 360 px breakpoint are really in the sheet;
 *   4. the queue rows are keyboard-reorderable, named, and bound at the ends;
 *   5. the table hands its renderers a row index (the reason reorder was broken);
 *   6. no icon-only button is nameless, and nothing is mouse-only.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { MIN_TARGET_PX } from '../lib/a11y.js';
import { DICT } from '../lib/i18n.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const read = (...p) => fs.readFileSync(path.join(FE, ...p), 'utf8');

const CSS_RAW = read('styles', 'global.css');
const CSS = CSS_RAW.replace(/\/\*[\s\S]*?\*\//g, '');
const QUEUE = read('pages', 'queue.js');
const TABLE = read('components', 'ui', 'DataTable.js');

/** Every rule header in the sheet, at-rules excluded. */
const headers = [...CSS.matchAll(/([^{}]+)\{[^{}]*\}/g)]
  .map((m) => m[1].trim())
  .filter((h) => !h.startsWith('@'));

/** Every selector, split out of the comma lists. */
const selectors = headers.flatMap((h) => h.split(',').map((s) => s.trim()));

test('every hover state has a keyboard twin', () => {
  const bases = selectors
    .filter((s) => s.includes(':hover'))
    .map((s) => s.replace(/:hover[^:]*$/, '').trim());
  assert.ok(bases.length > 0, 'the sheet still has hover states to pair');
  for (const base of bases) {
    const paired = selectors.some((s) => s === `${base}:focus-visible` || s === `${base}:focus-within`);
    assert.ok(paired, `${base}:hover has no :focus-visible or :focus-within twin`);
  }
});

test('nothing is revealed by hover alone', () => {
  const hoverBlocks = [...CSS.matchAll(/([^{}]*:hover[^{}]*)\{([^{}]*)\}/g)];
  assert.ok(hoverBlocks.length > 0);
  for (const [, selector, body] of hoverBlocks) {
    for (const hidden of [/display\s*:\s*none/, /visibility\s*:\s*hidden/, /opacity\s*:\s*0(?:[;\s}]|$)/]) {
      assert.doesNotMatch(body, hidden,
        `${selector.trim()} hides by hover — a touch or keyboard user could never reach it`);
    }
  }
});

test('the touch target floor and the 360 px breakpoint are in the sheet', () => {
  assert.match(CSS, new RegExp(`min-height:\\s*${MIN_TARGET_PX}px`));
  assert.match(CSS, new RegExp(`min-width:\\s*${MIN_TARGET_PX}px`));
  assert.match(CSS, /@media\s*\(max-width:\s*360px\)/);
  assert.match(CSS, /\(pointer:\s*coarse\)/);
  assert.match(CSS, /\.sr-only\s*\{/, 'the live region needs a visually-hidden class');
});


test('the queue rows are focusable and move on Alt+Arrow', () => {
  assert.match(QUEUE, /reorderRowProps\(/);
  assert.match(QUEUE, /rowProps=/);
  assert.match(QUEUE, /onMove:\s*move/);
  // The index the reorder needs comes from the render position, not a closure.
  assert.match(QUEUE, /rowProps=\{\(r, i\)/);
  // Both ends are bound: the first row cannot move up, the last cannot move down.
  assert.match(QUEUE, /disabled=\{i === 0\}/);
  assert.match(QUEUE, /disabled=\{i === entries\.length - 1\}/);
  // The move goes through the tested helper, never a hand-rolled swap.
  assert.match(QUEUE, /moveWithin\(ids, idx, dir\)/);
  assert.doesNotMatch(QUEUE, /\[ids\[idx\], ids\[j\]\]\s*=/, 'the undefined-index swap must not come back');
});

test('the reorder is announced, and the arrows are named', () => {
  assert.match(QUEUE, /role="status"/);
  assert.match(QUEUE, /aria-live="polite"/);
  assert.match(QUEUE, /aria-label=\{t\('moveUp'\) \+ ' ' \+ r\.token\}/);
  assert.match(QUEUE, /aria-label=\{t\('moveDown'\) \+ ' ' \+ r\.token\}/);
});

test('the table hands every renderer the row index', () => {
  assert.match(TABLE, /c\.render\(row, ri\)/);
  assert.match(TABLE, /rowProps\(row, ri\)/);
  assert.doesNotMatch(TABLE, /c\.render\(row\)/, 'the index-free call is what broke reorder');
});

test('the three new keys resolve in both languages', () => {
  for (const k of ['moveUp', 'moveDown', 'movedTo']) {
    assert.ok(DICT.bn[k], `${k} missing in bn`);
    assert.ok(DICT.en[k], `${k} missing in en`);
    assert.notEqual(DICT.bn[k], DICT.en[k], `${k} is the same string in both languages`);
  }
});

test('no icon-only button is nameless', () => {
  const files = [];
  for (const dir of ['pages', 'components']) {
    const walk = (rel) => {
      for (const entry of fs.readdirSync(path.join(FE, rel), { withFileTypes: true })) {
        const next = path.join(rel, entry.name);
        if (entry.isDirectory()) walk(next);
        else if (entry.name.endsWith('.js')) files.push(next);
      }
    };
    walk(dir);
  }
  const glyphs = /<button\b([\s\S]*?)>\s*[↑↓×✕✖→←]\s*<\/button>/g;
  let inspected = 0;
  for (const file of files) {
    const src = read(file);
    for (const [, attrs] of src.matchAll(glyphs)) {
      inspected += 1;
      assert.match(attrs, /aria-label/, `${file}: a glyph-only button has no accessible name`);
    }
  }
  assert.ok(inspected > 0, 'the scan must actually find the queue arrows');
});

test('nothing is mouse-only', () => {
  const walk = (rel) => {
    for (const entry of fs.readdirSync(path.join(FE, rel), { withFileTypes: true })) {
      const next = path.join(rel, entry.name);
      if (entry.isDirectory()) walk(next);
      else if (entry.name.endsWith('.js')) {
        assert.doesNotMatch(read(next), /onMouse(Enter|Over|Leave)/,
          `${next} gates behaviour on the pointer`);
      }
    }
  };
  for (const dir of ['pages', 'components', 'lib']) walk(dir);
});
