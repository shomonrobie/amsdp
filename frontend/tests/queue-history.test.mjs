/* MP-24 — the queue history screen.
 *
 * The page consumes the existing `GET /api/v1/queue/history`.  The query is
 * built by `lib/queue/history.js` so it can be tested without a browser, and the
 * page is asserted to use it rather than assemble URLs inline.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { STATUS_OPTIONS, historyQuery, summarise } from '../lib/queue/history.js';
import { DICT } from '../lib/i18n.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const REPO = path.resolve(FE, '..');

const PAGE = fs.readFileSync(path.join(FE, 'pages', 'queue-history.js'), 'utf8');
const MAIN = fs.readFileSync(
  path.join(REPO, 'backend', 'queuing', 'main.py'), 'utf8');

test('the query names only the parameters the route accepts', () => {
  assert.equal(historyQuery({ doctorId: 'd 1', day: '2026-11-26' }),
    '/api/v1/queue/history?doctor_id=d%201&date=2026-11-26');
  assert.equal(historyQuery({ doctorId: 'd1', day: '2026-11-26', status: 'completed',
    branchId: 'b1' }),
  '/api/v1/queue/history?doctor_id=d1&date=2026-11-26&status=completed&branch_id=b1');
  // An empty optional filter is omitted, not sent as an empty string: the server
  // reads an absent branch_id as "the caller's branch" and an absent status as
  // "every status", while '' is neither.
  assert.equal(historyQuery({ doctorId: 'd1', day: '2026-11-26', status: '', branchId: '' }),
    '/api/v1/queue/history?doctor_id=d1&date=2026-11-26');
});

test('the summary counts what the server sent, without re-classifying it', () => {
  const counts = summarise([
    { status: 'waiting' }, { status: 'waiting' }, { status: 'called' },
    { status: 'in_consultation' }, { status: 'skipped' },
    { status: 'completed' }, { status: 'completed' }, { status: 'completed' },
    { status: 'cancelled' }, { status: 'no_show' }, {},
  ]);
  assert.equal(counts.waiting, 2);
  assert.equal(counts.completed, 3, 'a completed entry is not folded into waiting');
  assert.equal(counts.skipped, 1, 'a skipped entry keeps its own status');
  assert.equal(counts.no_show, 1);
  assert.equal(counts.unknown, 1, 'a row without a status is counted, never dropped');
  assert.equal(Object.values(counts).reduce((a, b) => a + b, 0), 11);
});

test('every status option has a label in both languages', () => {
  assert.equal(STATUS_OPTIONS.length, 7);
  for (const option of STATUS_OPTIONS) {
    assert.ok(DICT.bn[option.labelKey] !== undefined, 'missing bn ' + option.labelKey);
    assert.ok(DICT.en[option.labelKey] !== undefined, 'missing en ' + option.labelKey);
  }
});

test('the page reads the endpoint through the shared query builder', () => {
  assert.ok(PAGE.indexOf('historyQuery(') >= 0, 'the query is not hand-assembled');
  assert.ok(PAGE.indexOf('summarise(') >= 0, 'the tally is not recomputed inline');
  assert.ok(PAGE.indexOf("'/api/v1/queue/history'") < 0,
    'no second, divergent copy of the path in the page');
  assert.ok(PAGE.indexOf("can('queue.view')") >= 0, 'gated on the capability the route uses');
});

test('the backend route still owns the scoping rules the screen relies on', () => {
  assert.ok(MAIN.indexOf('@app.get("/api/v1/queue/history")') >= 0);
  const route = MAIN.slice(MAIN.indexOf('@app.get("/api/v1/queue/history")'),
    MAIN.indexOf('@app.get("/api/v1/queue/history")') + 2200);
  assert.ok(/doctor_id: str = Query\(\.\.\.\)/.test(route), 'doctor_id is required');
  assert.ok(/date: str = Query\(\.\.\.\)/.test(route), 'date is required');
  assert.ok(route.indexOf('can_access_doctor') >= 0,
    'a doctor or assistant may only read their own queue');
  assert.ok(route.indexOf('branch_accessible(auth, branch_id)') >= 0,
    'a foreign branch is refused');
  assert.ok(route.indexOf('HTTPException(404') >= 0, 'and refused non-disclosingly');
  // History is every status: the route must not filter to the live ones.
  assert.ok(route.indexOf('ACTIVE_STATUSES') < 0, 'history must not hide terminal entries');
});

test('the identifiers a browser suite needs are present', () => {
  for (const id of ['history-heading', 'history-branch', 'history-doctor', 'history-date',
    'history-status', 'history-table', 'history-prev', 'history-next']) {
    assert.ok(PAGE.indexOf('data-testid="' + id + '"') >= 0, 'missing testid ' + id);
  }
  for (const id of ["'history-row-'", "'history-summary'", "'history-empty'"]) {
    assert.ok(PAGE.indexOf('data-testid={' + id) >= 0
      || PAGE.indexOf('data-testid="' + id.slice(1, -1) + '"') >= 0,
    'missing testid ' + id);
  }
});
