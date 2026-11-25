/* MP-22 — the dashboard's decisions, without a browser.
 *
 * The screen is JSX and this repository ships no DOM renderer, so the rules that
 * decide what it offers live in `lib/dashboard.js` where they can be asserted:
 * which branches the selector may list, which shortcuts a role gets, how the
 * query strings are built, and how an audit event becomes a row.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  activityQuery, activityRow, activityRows, dashboardQuery, mayChooseAnyBranch,
  perDoctorRows, quickActionsFor, selectableBranches,
} from '../lib/dashboard.js';

const BRANCHES = [
  { id: 'br-1', name: 'Main', status: 'active' },
  { id: 'br-2', name: 'Annex', status: 'active' },
  { id: 'br-3', name: 'Closed wing', status: 'inactive' },
];

test('an organization administrator may choose any active branch', () => {
  const user = { role: 'org_admin', branch_id: 'br-1' };
  assert.equal(mayChooseAnyBranch(user), true);
  assert.deepEqual(selectableBranches(BRANCHES, user).map((b) => b.id), ['br-1', 'br-2']);
});

test('a branch user is offered their own branch only', () => {
  const user = { role: 'receptionist', branch_id: 'br-2' };
  assert.equal(mayChooseAnyBranch(user), false);
  assert.deepEqual(selectableBranches(BRANCHES, user).map((b) => b.id), ['br-2']);
});

test('a branch user whose branch is not in the roster gets an empty list, not all of it', () => {
  const user = { role: 'receptionist', branch_id: 'br-9' };
  assert.deepEqual(selectableBranches(BRANCHES, user), []);
});

test('a branch-scoped user with no branch on the token is offered nothing', () => {
  assert.deepEqual(selectableBranches(BRANCHES, { role: 'doctor' }), []);
});

test('inactive branches are never offered', () => {
  const user = { role: 'super_admin' };
  assert.deepEqual(selectableBranches(BRANCHES, user).map((b) => b.id), ['br-1', 'br-2']);
});

test('a malformed roster is empty rather than fatal', () => {
  assert.deepEqual(selectableBranches(null, { role: 'org_admin' }), []);
  assert.deepEqual(selectableBranches([null, undefined], { role: 'org_admin' }), []);
});

test('a doctor is offered the queue and booking shortcuts, not registration', () => {
  const keys = quickActionsFor({ role: 'doctor' }).map((a) => a.key);
  assert.deepEqual(keys, ['newAppointment', 'queue']);
  assert.deepEqual(quickActionsFor({ role: 'assistant' }).map((a) => a.key), keys);
});

test('front-desk and administrative roles get all four shortcuts', () => {
  const keys = quickActionsFor({ role: 'receptionist' }).map((a) => a.key);
  assert.deepEqual(keys, ['newAppointment', 'queue', 'patients', 'schedules']);
  assert.deepEqual(quickActionsFor({ role: 'org_admin' }).map((a) => a.key), keys);
});

test('the today query carries the chosen branch and day, and nothing when unset', () => {
  assert.equal(dashboardQuery({}), '');
  assert.equal(dashboardQuery({ branchId: 'br-1' }), '?branch_id=br-1');
  assert.equal(dashboardQuery({ date: '2026-11-24' }), '?date=2026-11-24');
  assert.equal(dashboardQuery({ branchId: 'br 1', date: '2026-11-24' }),
    '?branch_id=br%201&date=2026-11-24');
});

test('the activity query always bounds the panel, and scopes it when a branch is chosen', () => {
  assert.equal(activityQuery({}), '?limit=8');
  assert.equal(activityQuery({ limit: 5 }), '?limit=5');
  assert.equal(activityQuery({ branchId: 'br-1', limit: 3 }), '?limit=3&branch_id=br-1');
});

test('a known audit action becomes a label key, an unknown one keeps its own name', () => {
  assert.equal(activityRow({ action: 'queue.call' }).labelKey, 'queue');
  const unknown = activityRow({ action: 'something.new', actor_id: 'u1' });
  assert.equal(unknown.labelKey, '');
  assert.equal(unknown.action, 'something.new');
  assert.equal(unknown.actor, 'u1');
});

test('activity rows survive a malformed payload without throwing', () => {
  assert.deepEqual(activityRows(null), []);
  const [row] = activityRows([{}]);
  assert.equal(row.action, '');
  assert.equal(row.labelKey, '');
});

test('the per-doctor panel is ordered by volume and named from the roster', () => {
  const today = { per_doctor: [
    { doctor_id: 'doc-1', count: 2 },
    { doctor_id: 'doc-2', count: 5 },
  ] };
  const rows = perDoctorRows(today, { 'doc-1': 'Dr. A', 'doc-2': 'Dr. B' });
  assert.deepEqual(rows.map((r) => [r.name, r.count]), [['Dr. B', 5], ['Dr. A', 2]]);
});

test('an unnamed doctor falls back to the id rather than an empty cell', () => {
  const rows = perDoctorRows({ per_doctor: [{ doctor_id: 'doc-9', count: 1 }] }, {});
  assert.equal(rows[0].name, 'doc-9');
});

test('no per-doctor data is an empty panel, not a crash', () => {
  assert.deepEqual(perDoctorRows(null), []);
  assert.deepEqual(perDoctorRows({}), []);
});
