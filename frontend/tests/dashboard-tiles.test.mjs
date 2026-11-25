/* Dashboard "today" tiles — one tile per figure, no shared binding.
 *
 * MP-07 / GAP-04: the Waiting tile was bound to `today.checked_in`, the same
 * figure as the adjacent Checked-in tile, so the two cards were always
 * identical and a queued-but-not-called patient changed nothing. A dashboard
 * that silently shows one number twice is worse than one with a missing card.
 *
 * The page is JSX and this project ships no DOM test renderer (see the note in
 * `queue-call-control.test.mjs`), so the contract is asserted against the page
 * source: the tile list, each tile's bound field, and the absence of a
 * duplicate binding.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const PAGE = fs.readFileSync(path.join(FE, 'pages', 'dashboard.js'), 'utf8');

/** The `{ label: t('…'), value: today.<field> || 0 }` entries, in page order. */
function tiles() {
  const out = [];
  const re = /\{\s*label:\s*t\('([^']+)'\),\s*value:\s*today\.([A-Za-z0-9_]+)\s*\|\|\s*0\s*\}/g;
  let m;
  while ((m = re.exec(PAGE)) !== null) out.push({ label: m[1], field: m[2] });
  return out;
}

test('the dashboard declares its six today tiles', () => {
  const t = tiles();
  assert.equal(t.length, 6, 'tiles found: ' + JSON.stringify(t));
  assert.deepEqual(t.map((x) => x.label),
    ['booked', 'checkedIn', 'waiting', 'completedT', 'cancelledT', 'noShow']);
});

test('the Waiting tile counts the queue, not the check-in tally', () => {
  const waiting = tiles().find((x) => x.label === 'waiting');
  assert.ok(waiting, 'no Waiting tile found');
  assert.equal(waiting.field, 'in_queue',
    'MP-07: Waiting must read today.in_queue, found today.' + waiting.field);
});

test('no two tiles display the same figure', () => {
  const fields = tiles().map((x) => x.field);
  assert.equal(new Set(fields).size, fields.length,
    'duplicate tile binding: ' + fields.join(', '));
});
