/* MP-23 — the operational reporting screen (BR §43).
 *
 * The endpoint is asserted by `backend/tests/test_operational_reports.py`; this
 * file guards the half those tests cannot reach: the screen must ask the route the
 * questions it answers, print the figures it publishes, and claim reconciliation
 * only when the payload's own identities hold.
 *
 * Three things are read from the backend source rather than trusted:
 *   * the period ceiling (`MAX_PERIOD_DAYS`), so the screen cannot offer a range
 *     the route will refuse;
 *   * the headline figures (`HEADLINE`), so a figure the server stops sending
 *     cannot silently disappear from the page;
 *   * the lifecycle and queue vocabularies, so every status the report can print
 *     has a Bangla and an English label.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  DIMENSIONS, HEADLINE_KEYS, HEADLINE_ORDER, MAX_PERIOD_DAYS, QUEUE_METRICS,
  QUEUE_STATE_LABELS, REPORT_PATH, STATUS_LABELS, isEmptyReport, isoDay,
  minutesText, percentText, periodInverted, periodTooLong, queueStateRows,
  reconciles, reportQuery, scopeOf, statusRows, utilisationRows,
} from '../lib/operational-report.js';
import { DICT } from '../lib/i18n.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const REPO = path.resolve(FE, '..');

const PAGE = fs.readFileSync(path.join(FE, 'pages', 'reports.js'), 'utf8');
const LIB = fs.readFileSync(path.join(FE, 'lib', 'operational-report.js'), 'utf8');
const REPORTS = fs.readFileSync(
  path.join(REPO, 'backend', 'appointment', 'reports.py'), 'utf8');
const MAIN = fs.readFileSync(
  path.join(REPO, 'backend', 'appointment', 'main.py'), 'utf8');
const CONFIG = fs.readFileSync(path.join(FE, 'next.config.js'), 'utf8');

/** A quoted tuple such as `LIFECYCLE = ("BOOKED", ...)`, read from the source. */
function pythonTuple(name) {
  const at = REPORTS.indexOf(name);
  assert.ok(at >= 0, name + ' is not declared in reports.py');
  const block = REPORTS.slice(at, REPORTS.indexOf(')', at));
  return [...block.matchAll(/"([A-Za-z_]+)"/g)].map((m) => m[1]);
}

/** The `HEADLINE` mapping's figure names, in the order the endpoint emits them. */
function headlineNames() {
  const start = REPORTS.indexOf('HEADLINE = OrderedDict(');
  const end = REPORTS.indexOf('PRESENT = (', start);
  assert.ok(start >= 0 && end > start, 'HEADLINE could not be located');
  return [...REPORTS.slice(start, end).matchAll(/\("([a-z_]+)", \(/g)].map((m) => m[1]);
}

/** A payload shaped like the endpoint's answer. */
function payload(overrides = {}) {
  const base = {
    from: '2026-03-10', to: '2026-03-10', facility_today: '2026-03-10',
    branch_id: null, requested_branch_id: null, doctor_id: null,
    appointments: {
      total: 3,
      by_day: [{ date: '2026-03-10', count: 3 }],
      by_doctor: [{ doctor_id: 'doc-1', count: 3 }],
      by_branch: [{ branch_id: 'br-1', count: 3 }],
    },
    status_counts: { BOOKED: 1, COMPLETED: 1, CANCELLED: 1 },
    br43: { booked: 1, completed: 1, cancelled: 1, no_show: 0, present: 0 },
    walk_ins: 1,
    booking_sources: [{ source: 'walk_in', count: 1 }, { source: 'phone', count: 2 }],
    queue_activity: {
      entries: 2,
      by_status: { waiting: 1, completed: 1 },
      by_source: [{ source: 'appointment', count: 2 }],
      calls: 1, transitions: 2, avg_wait_minutes: 10.0, avg_service_minutes: 15.0,
    },
    utilisation: {
      capacity: 4, claimed: 2, unscheduled: 1, percent: 50.0, days: 1,
      by_doctor: [{ doctor_id: 'doc-1', capacity: 4, claimed: 2,
        unscheduled: 1, percent: 50.0 }],
    },
    reconciliation: {
      appointments_total: 3, status_sum: 3, by_day_sum: 3, by_doctor_sum: 3,
      by_branch_sum: 3, booking_sources_sum: 3, queue_entries: 2, queue_status_sum: 2,
    },
  };
  return Object.assign(base, overrides);
}

test('the screen asks the endpoint the route actually publishes', () => {
  assert.ok(REPORTS.includes('router = APIRouter(prefix="/api/v1/reports"'),
    'the reports router prefix changed');
  assert.ok(REPORTS.includes('@router.get("/operational")'),
    'the operational route changed');
  assert.equal(REPORT_PATH, '/api/v1/reports/operational');
  assert.ok(MAIN.includes('include_router(reports_router)'),
    'the reports router is not mounted, so the screen has nothing to call');
  assert.ok(CONFIG.includes("'/api/v1/reports/:path*'"),
    'the browser origin does not proxy /api/v1/reports');
  assert.ok(PAGE.includes('reportQuery('),
    'the page must build its query through the tested module');
  assert.equal(/(?<![\w.])fetch\s*\(/.test(PAGE), false,
    'the page must use apiFetch, which carries the token and the 401 handling');
});

test('the period ceiling is the backend constant, not a guess', () => {
  const declared = Number((REPORTS.match(/MAX_PERIOD_DAYS = (\d+)/) || [])[1]);
  assert.ok(declared > 0, 'MAX_PERIOD_DAYS did not parse');
  assert.equal(MAX_PERIOD_DAYS, declared);
  assert.equal(periodTooLong('2026-01-01', '2026-01-01'), false);
  assert.equal(periodTooLong('2026-01-01', '2026-12-31'), false, '365 days is allowed');
  assert.equal(periodTooLong('2024-01-01', '2026-01-02'), true);
  assert.equal(periodInverted('2026-03-11', '2026-03-10'), true);
  assert.equal(periodInverted('2026-03-10', '2026-03-10'), false);
  assert.equal(periodInverted('', '2026-03-10'), false);
});

test('the query never asks for a day and a period at once', () => {
  assert.equal(reportQuery({ mode: 'day', day: '2026-03-10' }),
    REPORT_PATH + '?date=2026-03-10');
  assert.equal(reportQuery({ mode: 'range', from: '2026-03-01', to: '2026-03-03' }),
    REPORT_PATH + '?from_date=2026-03-01&to_date=2026-03-03');
  const both = reportQuery({ mode: 'day', day: '2026-03-10',
    from: '2026-03-01', to: '2026-03-03' });
  assert.equal(both.includes('from_date'), false,
    'the route answers 422 when a day and a period are both given');
  assert.equal(reportQuery({ mode: 'day', day: '2026-03-10', branchId: 'br-1',
    doctorId: 'doc-1' }),
  REPORT_PATH + '?date=2026-03-10&branch_id=br-1&doctor_id=doc-1');
  assert.equal(reportQuery({ mode: 'day', day: '2026-03-10', branchId: '',
    doctorId: null }), REPORT_PATH + '?date=2026-03-10',
  'an empty filter must be omitted, not sent blank');
  assert.equal(reportQuery({ mode: 'day' }), REPORT_PATH,
    'no date means the facility today, which the route resolves');
});


test('a percentage with no denominator is printed as no figure, never as 0%', () => {
  assert.equal(percentText(null), '—');
  assert.equal(percentText(undefined), '—');
  assert.equal(percentText(''), '—');
  assert.equal(percentText(0), '0%', 'a real zero is still a figure');
  assert.equal(percentText(50), '50%');
  assert.equal(percentText(133.3), '133.3%', 'a day may honestly exceed 100%');
  assert.equal(percentText('not a number'), '—');
  assert.equal(minutesText(null), '—');
  assert.equal(minutesText(10), '10');
  assert.equal(minutesText(0), '0');
});

test('reconciliation is computed from the payload, not assumed', () => {
  const good = payload();
  assert.deepEqual(reconciles(good), { ok: true, problems: [] });

  const bad = payload({
    reconciliation: Object.assign({}, good.reconciliation, { by_branch_sum: 4 }),
  });
  const badCheck = reconciles(bad);
  assert.equal(badCheck.ok, false);
  assert.deepEqual(badCheck.problems, ['by_branch_sum']);

  const noBlock = payload();
  delete noBlock.reconciliation;
  assert.deepEqual(reconciles(noBlock), { ok: false, problems: ['reconciliation'] });

  const inconsistentTotal = payload({
    appointments: Object.assign({}, good.appointments, { total: 4 }),
  });
  assert.deepEqual(reconciles(inconsistentTotal).problems, ['appointments_total']);

  const queueMismatch = payload({
    reconciliation: Object.assign({}, good.reconciliation, { queue_status_sum: 9 }),
  });
  assert.deepEqual(reconciles(queueMismatch).problems, ['queue_status_sum']);
  assert.equal(reconciles(null).ok, false);
});

test('an empty day is reported as empty, and the figures are still zeroes', () => {
  const empty = payload({
    appointments: { total: 0, by_day: [], by_doctor: [], by_branch: [] },
    status_counts: {},
    br43: { booked: 0, completed: 0, cancelled: 0, no_show: 0, present: 0 },
    walk_ins: 0,
    booking_sources: [],
    queue_activity: { entries: 0, by_status: {}, by_source: [], calls: 0,
      transitions: 0, avg_wait_minutes: null, avg_service_minutes: null },
    utilisation: { capacity: 0, claimed: 0, unscheduled: 0, percent: null,
      days: 1, by_doctor: [] },
    reconciliation: { appointments_total: 0, status_sum: 0, by_day_sum: 0,
      by_doctor_sum: 0, by_branch_sum: 0, booking_sources_sum: 0,
      queue_entries: 0, queue_status_sum: 0 },
  });
  assert.equal(isEmptyReport(empty), true);
  assert.equal(reconciles(empty).ok, true, 'zero equals zero: an empty day reconciles');
  assert.equal(percentText(empty.utilisation.percent), '—');
  assert.deepEqual(statusRows(empty.status_counts), []);
  assert.deepEqual(utilisationRows(empty.utilisation), []);
  assert.equal(isEmptyReport(payload()), false);
});

test('rows keep the order the endpoint published', () => {
  const rows = statusRows(payload().status_counts);
  assert.deepEqual(rows.map((r) => r.status), ['BOOKED', 'COMPLETED', 'CANCELLED']);
  assert.deepEqual(rows.map((r) => r.count), [1, 1, 1]);
  assert.equal(rows[0].labelKey, 'repStBooked');
  assert.deepEqual(queueStateRows(payload().queue_activity.by_status)
    .map((r) => r.state), ['waiting', 'completed']);
  const unknown = statusRows({ SOMETHING_NEW: 2 });
  assert.deepEqual(unknown, [{ status: 'SOMETHING_NEW', labelKey: '', count: 2 }],
    'an unknown status is printed as its code rather than dropped');
});

test('the scope shown is the scope the server resolved', () => {
  const narrowed = scopeOf(payload({ branch_id: 'br-1' }));
  assert.equal(narrowed.branchId, 'br-1');
  assert.equal(narrowed.requestedBranchId, '');
  assert.equal(narrowed.narrowed, true,
    'a branch-scoped principal is narrowed to its own branch by the route');
  const asked = scopeOf(payload({ branch_id: 'br-1', requested_branch_id: 'br-1' }));
  assert.equal(asked.narrowed, false);
  assert.equal(scopeOf({}).from, '');
  assert.equal(isoDay('2026-03-10T00:00:00Z').length, 10);
  assert.equal(isoDay('not a date'), '');
});


test('the headline figures are the ones the endpoint publishes', () => {
  const names = headlineNames();
  assert.deepEqual(names, ['booked', 'completed', 'cancelled', 'no_show'],
    'BR §43 headline counts changed in reports.py');
  assert.deepEqual([...HEADLINE_ORDER], names.concat(['present']),
    'the screen must show every headline figure, plus the present-in-facility count');
  for (const name of HEADLINE_ORDER) {
    assert.ok(HEADLINE_KEYS[name], name + ' has no label key');
    assert.ok(DICT.bn[HEADLINE_KEYS[name]], name + ' has no Bangla label');
    assert.ok(DICT.en[HEADLINE_KEYS[name]], name + ' has no English label');
  }
  assert.ok(!HEADLINE_ORDER.includes('revenue') && !HEADLINE_ORDER.includes('payment'),
    'BR §43 forbids money figures');
});

test('every status and queue state the report can print has a label', () => {
  const lifecycle = pythonTuple('LIFECYCLE = (');
  assert.ok(lifecycle.length >= 10, 'LIFECYCLE did not parse');
  for (const status of lifecycle) {
    const key = STATUS_LABELS[status];
    assert.ok(key, status + ' has no label key, so the report would print a raw code');
    assert.ok(DICT.bn[key], status + ' has no Bangla label');
    assert.ok(DICT.en[key], status + ' has no English label');
  }
  const states = pythonTuple('QUEUE_STATES = (');
  assert.ok(states.length >= 7, 'QUEUE_STATES did not parse');
  for (const state of states) {
    const key = QUEUE_STATE_LABELS[state];
    assert.ok(key, state + ' has no label key');
    assert.ok(DICT.bn[key] && DICT.en[key], state + ' is missing a translation');
  }
  assert.deepEqual(pythonTuple('PRESENT = ('),
    ['CHECKED_IN', 'IN_QUEUE', 'IN_CONSULTATION']);
});

test('every dimension and queue metric the screen shows has a label', () => {
  assert.equal(DIMENSIONS.length, 5, 'BR §43 has five permitted dimensions');
  for (const dimension of DIMENSIONS) {
    assert.ok(DICT.bn[dimension.labelKey], dimension.key + ' has no Bangla title');
    assert.ok(DICT.en[dimension.labelKey], dimension.key + ' has no English title');
  }
  for (const metric of QUEUE_METRICS) {
    assert.ok(DICT.bn[metric.labelKey], metric.key + ' has no Bangla label');
    assert.ok(DICT.en[metric.labelKey], metric.key + ' has no English label');
  }
  /* The queue block the screen reads must exist in the payload before it is used. */
  for (const metric of QUEUE_METRICS) {
    assert.ok(REPORTS.includes('"' + metric.key + '"'),
      'reports.py does not publish queue_activity.' + metric.key);
  }
});

test('the screen prints the report and no invented figure', () => {
  for (const testid of ['rep-headline', 'rep-status', 'rep-appointments',
    'rep-walkins', 'rep-queue', 'rep-utilisation', 'rep-reconciliation']) {
    assert.ok(PAGE.includes('testid="' + testid + '"'), testid + ' is not rendered');
  }
  assert.ok(PAGE.includes('reconciles(data)'),
    'the reconciliation panel must re-check the payload');
  assert.ok(PAGE.includes('percentText('),
    'percentages must go through the null-safe formatter');
  assert.equal(/speechSynthesis|synthesis/i.test(PAGE), false,
    'a report screen has no business starting speech');
  /* The one thing BR §43 forbids: money and clinical-performance analytics. */
  assert.equal(/revenue|invoice|billing|settlement|profit|margin/i.test(PAGE), false,
    'BR §43 forbids revenue, billing and settlement figures');
  assert.equal(/revenue|billing|payment_settlement/i.test(LIB), false);
});

