/* The client-side permission mirror, compared with the server matrix.
 *
 * `frontend/lib/auth.js` carries a copy of `backend/common/permissions.py` so the
 * interface can hide what the server would refuse.  A copy is only worth having if
 * it is *the same*: MP-04's voice-pack screen asked for `org.read`, which the
 * mirror withheld from `org_admin` while the server granted it, so the one role
 * that may configure a facility's voice was shown a permission refusal — and no
 * test noticed, because the page was never opened with that role.
 *
 * This test parses the Python matrix and fails on any divergence, in either
 * direction.  The mirror is still not the boundary: every route checks again.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { ROLE_PERMISSIONS, hasPermission } from '../lib/auth.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..', '..');
const SRC = fs.readFileSync(
  path.join(REPO, 'backend', 'common', 'permissions.py'), 'utf8');

/** `PERMISSIONS` as `role -> string[]`, read from the Python source. */
function serverMatrix() {
  const start = SRC.indexOf('PERMISSIONS: dict');
  const end = SRC.indexOf('#: Capabilities an administrator may grant');
  assert.ok(start >= 0 && end > start, 'PERMISSIONS could not be located');
  const body = SRC.slice(start, end);

  const platform = [...SRC.slice(SRC.indexOf('PLATFORM_CAPABILITIES: tuple'),
    SRC.indexOf('PERMISSIONS: dict')).matchAll(/"([a-z_.]+)"/g)]
    .map((m) => m[1]);

  const out = {};
  for (const match of body.matchAll(/"([a-z_]+)": \[([\s\S]*?)\],/g)) {
    const role = match[1];
    // Comments quote capability names ("gated on doctor.manage"), so they must be
    // removed before the list is read — otherwise a comment becomes a grant.
    const block = match[2].replace(/#[^\n]*/g, '');
    const perms = [...block.matchAll(/"([a-z_.*]+)"/g)].map((m) => m[1]);
    if (block.includes('*PLATFORM_CAPABILITIES')) perms.push(...platform);
    out[role] = perms;
  }
  return out;
}

const SERVER = serverMatrix();

test('the matrix parses, and the roles are the ones the mirror declares', () => {
  assert.ok(Object.keys(SERVER).length >= 6,
    'parsed only ' + Object.keys(SERVER).join(', '));
  assert.deepEqual(Object.keys(SERVER).sort(), Object.keys(ROLE_PERMISSIONS).sort());
  assert.ok(SERVER.super_admin.includes('platform.admin')
    && SERVER.super_admin.includes('platform.cross_org'),
  'the PLATFORM_CAPABILITIES expansion did not parse');
});

test('every role holds exactly the capabilities the server grants', () => {
  for (const role of Object.keys(SERVER)) {
    const server = [...new Set(SERVER[role])].sort();
    const mirror = [...ROLE_PERMISSIONS[role]].sort();
    const missing = server.filter((p) => !mirror.includes(p));
    const extra = mirror.filter((p) => !server.includes(p));
    assert.deepEqual(missing, [], role + ' is missing: ' + missing.join(', '));
    assert.deepEqual(extra, [], role + ' invents: ' + extra.join(', '));
  }
});

test('a capability resolves the same way on both sides', () => {
  const granted = (perms, perm) => perms.some((p) => perm === p
    || (p.endsWith('.*') && perm.startsWith(p.slice(0, -1))));
  const probes = ['org.read', 'org.manage', 'platform.admin', 'queue.display.manage',
    'appointment.read', 'appointment.check_in', 'audit.read', 'patient.update',
    'staff.manage', 'queue.consult', 'facility.manage', 'nothing.at.all'];
  for (const role of Object.keys(SERVER)) {
    for (const perm of probes) {
      assert.equal(hasPermission({ role }, perm), granted(SERVER[role], perm),
        role + ' · ' + perm);
    }
  }
});

test('an unknown or absent role holds nothing', () => {
  assert.equal(hasPermission({ role: 'auditor' }, 'audit.read'), false);
  assert.equal(hasPermission(null, 'org.read'), false);
  assert.equal(hasPermission({}, 'org.read'), false);
  assert.equal(hasPermission({ role: 'super_admin' }, 'org.read'), true);
  assert.equal(hasPermission({ role: 'receptionist' }, 'org.manage'), false,
    'the front desk never configures an organization');
});
