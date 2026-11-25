/* Dashboard "today" tiles — one tile per figure, no shared binding.
 *
 * MP-07 / GAP-04: the Waiting tile was bound to `today.checked_in`, the same
 * figure as the adjacent Checked-in tile, so the two cards were always
 * identical and a queued-but-not-called patient changed nothing. A dashboard
 * that silently shows one number twice is worse than one with a missing card.
 *
 * Q-2 (Product Owner, 2026-11-25): the fix then bound Waiting to
 * `today.in_queue`, which counts *appointment records* in status IN_QUEUE. A
 * walk-in enqueued without an appointment row — the person most likely to be
 * standing in the room — raises `queue_length` and not `in_queue`, so the tile
 * and the waiting-room board disagreed by exactly the walk-ins. The approved
 * contract is: anything labelled "Waiting" reads `queue_length` (live queue
 * entries); `in_queue` stays visible under its own label as an appointment-status
 * count. Both are asserted below, because the failure mode is an alias.
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
  assert.equal(waiting.field, 'queue_length',
    'Q-2: Waiting must read today.queue_length (live queue entries), found ' +
    'today.' + waiting.field);
});

test('the appointment-status count is still shown, under its own label', () => {
  /* Q-2: `in_queue` must stay visible — it is a different question, not a
   * synonym. It is not a tile (six tiles are pinned above), so it is rendered
   * in the queue panel with its own i18n key. */
  assert.ok(!tiles().some((x) => x.field === 'in_queue'),
    'in_queue must not be offered as the Waiting figure');
  assert.match(PAGE, /t\('inQueueRecords'\)\}\s*:\s*\{today\.in_queue/,
    'the queue panel must publish today.in_queue under the inQueueRecords label');
});

test('no two tiles display the same figure', () => {
  const fields = tiles().map((x) => x.field);
  assert.equal(new Set(fields).size, fields.length,
    'duplicate tile binding: ' + fields.join(', '));
});
