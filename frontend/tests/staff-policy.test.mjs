/* MP-19 / MP-20 — the staff screen's decision rules.
 *
 * The page is JSX and this project ships no DOM test renderer (the same note is
 * in `dashboard-tiles.test.mjs`), so everything that *decides* something about
 * staff administration is extracted into `lib/staff-policy.js` and asserted
 * here.  The rendered behaviour — the list, the dialog, the grant buttons, the
 * denials — is covered by the Playwright suite in `e2e/`, not by this file.
 *
 * What is pinned:
 *  - the client role ladder agrees with the server's ROLE_HIERARCHY;
 *  - a caller is never offered a role at or above their own (self-escalation);
 *  - capability grants are offered only to organization administrators, because
 *    that is who the server lets grant them;
 *  - the labels map covers every capability the server's catalogue can return;
 *  - the form pre-flight rejects the same inputs the server would.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import {
  ROLE_LEVEL, ROLE_ORDER, canOfferRole, grantableRoles, mayGrantCapabilities,
  needsBranch, capabilityLabelKey, assignedDoctorIds, isActiveStatus,
  validateNewStaff, staffMatchesFilter, CAPABILITY_LABEL_KEYS,
} from '../lib/staff-policy.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const PERMISSIONS_PY = join(HERE, '..', '..', 'backend', 'common', 'permissions.py');

function serverTuple(name) {
  const source = readFileSync(PERMISSIONS_PY, 'utf8');
  const match = new RegExp(`${name}[^=]*= \\(([\\s\\S]*?)\\)`).exec(source);
  assert.ok(match, `${name} not found in permissions.py`);
  return [...match[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]);
}

test('the client role ladder matches the server hierarchy', () => {
  const source = readFileSync(PERMISSIONS_PY, 'utf8');
  const match = /ROLE_HIERARCHY[^=]*= \{([\s\S]*?)\}/.exec(source);
  assert.ok(match, 'ROLE_HIERARCHY not found in permissions.py');
  const server = Object.fromEntries(
    [...match[1].matchAll(/"([a-z_]+)":\s*(\d+)/g)].map((m) => [m[1], Number(m[2])]));
  assert.deepEqual(server, { ...ROLE_LEVEL },
    'the screen and the server must agree on the role ladder');
  assert.deepEqual([...ROLE_ORDER], [...ROLE_ORDER].sort(
    (a, b) => ROLE_LEVEL[a] - ROLE_LEVEL[b]));
});

test('every delegable capability the server can return has a label', () => {
  const delegable = serverTuple('DELEGABLE_CAPABILITIES');
  assert.ok(delegable.length >= 3, 'the delegable set should not be empty');
  for (const capability of delegable) {
    assert.ok(CAPABILITY_LABEL_KEYS[capability],
      `no label key for ${capability} — the screen would show the raw name`);
  }
  // The catalogue is closed: a label must not promise something ungrantable.
  for (const capability of Object.keys(CAPABILITY_LABEL_KEYS)) {
    assert.ok(delegable.includes(capability),
      `${capability} has a label but the server refuses it`);
  }
});
test('a caller is never offered a role at or above their own', () => {
  // org_admin may create a branch admin — below them — but never a peer or a
  // super administrator.  This is the UI half of PO-RBAC-03; the server refuses
  // the same combinations with 403.
  assert.equal(canOfferRole('org_admin', 'branch_admin'), true);
  assert.equal(canOfferRole('org_admin', 'receptionist'), true);
  assert.equal(canOfferRole('org_admin', 'org_admin'), false);
  assert.equal(canOfferRole('org_admin', 'super_admin'), false);
  assert.equal(canOfferRole('branch_admin', 'receptionist'), true);
  assert.equal(canOfferRole('branch_admin', 'branch_admin'), false);
  // The ladder alone would let a receptionist assign a doctor.  It is not the
  // gate: ``staff.manage`` is, and a receptionist does not hold it (403), which
  // is why the screen keys the management controls off the permission, not off
  // the ladder.  Asserted explicitly so nobody "fixes" the ladder to compensate.
  assert.equal(canOfferRole('receptionist', 'doctor'), true);
  assert.equal(canOfferRole('org_admin', 'not_a_role'), false);
});

test('the super administrator may offer every role', () => {
  assert.deepEqual(grantableRoles('super_admin'), [...ROLE_ORDER]);
});

test('each role sees only the roles it may assign', () => {
  assert.deepEqual(grantableRoles('org_admin'),
    ['assistant', 'doctor', 'receptionist', 'branch_admin']);
  assert.deepEqual(grantableRoles('receptionist'), ['assistant', 'doctor']);
});

test('only organization administrators are offered capability grants', () => {
  assert.equal(mayGrantCapabilities('org_admin'), true);
  assert.equal(mayGrantCapabilities('super_admin'), true);
  assert.equal(mayGrantCapabilities('branch_admin'), false,
    'a branch administrator administers the very boundary the grant crosses');
  assert.equal(mayGrantCapabilities('receptionist'), false);
});

test('branch-scoped roles ask for a branch and organization roles do not', () => {
  assert.equal(needsBranch('receptionist'), true);
  assert.equal(needsBranch('assistant'), true);
  assert.equal(needsBranch('branch_admin'), true);
  assert.equal(needsBranch('org_admin'), false);
  assert.equal(needsBranch('super_admin'), false);
});

test('an unknown capability falls back to its own name', () => {
  assert.equal(capabilityLabelKey('appointment.check_in'), 'capCheckIn');
  assert.equal(capabilityLabelKey('something.else'), 'something.else');
});

test('assigned doctors come from the list, then the legacy single field', () => {
  assert.deepEqual(assignedDoctorIds({ doctor_ids: ['d1', 'd2'] }), ['d1', 'd2']);
  assert.deepEqual(assignedDoctorIds({ doctor_id: 'd1' }), ['d1']);
  assert.deepEqual(assignedDoctorIds({ doctor_ids: [] , doctor_id: 'd1' }), []);
  assert.deepEqual(assignedDoctorIds(null), []);
});

test('status defaults to active so an old row is not hidden as inactive', () => {
  assert.equal(isActiveStatus(undefined), true);
  assert.equal(isActiveStatus('active'), true);
  assert.equal(isActiveStatus('inactive'), false);
});

test('the create pre-flight rejects what the server would reject', () => {
  const good = { username: 'clerk', password: 'longenough', display_name: 'Clerk', role: 'receptionist', branch_id: 'br-1' };
  assert.deepEqual(validateNewStaff(good, { branchRequired: true }), { ok: true, fields: [], passwordTooShort: false });

  const noUsername = validateNewStaff({ ...good, username: '  ' });
  assert.equal(noUsername.ok, false);
  assert.deepEqual(noUsername.fields, ['username']);

  const shortPassword = validateNewStaff({ ...good, password: 'short' });
  assert.equal(shortPassword.ok, false);
  assert.equal(shortPassword.passwordTooShort, true);

  const noBranch = validateNewStaff({ ...good, branch_id: '' }, { branchRequired: true });
  assert.deepEqual(noBranch.fields, ['branch_id']);

  const noRole = validateNewStaff({ ...good, role: 'wizard' });
  assert.deepEqual(noRole.fields, ['role']);
});

test('the roster filter matches names case-insensitively and honours status', () => {
  const clerk = { username: 'Rahim', display_name: 'রহিম উদ্দিন', role: 'receptionist', status: 'active', mobile: '01700000000' };
  assert.equal(staffMatchesFilter(clerk, { q: 'rahim' }), true);
  assert.equal(staffMatchesFilter(clerk, { q: 'উদ্দিন' }), true);
  assert.equal(staffMatchesFilter(clerk, { q: '0170' }), true);
  assert.equal(staffMatchesFilter(clerk, { q: 'karim' }), false);
  assert.equal(staffMatchesFilter(clerk, { role: 'receptionist' }), true);
  assert.equal(staffMatchesFilter(clerk, { role: 'doctor' }), false);
  assert.equal(staffMatchesFilter(clerk, { status: 'inactive' }), false);
  assert.equal(staffMatchesFilter({ ...clerk, status: 'inactive' }, { status: 'inactive' }), true);
});


