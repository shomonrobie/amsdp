/* MP-19 / MP-20 — the staff administration screen.
 *
 * What this file proves, and how:
 *   - the *rules* the screen offers are real, tested code (`lib/staff-policy.js`,
 *     covered by `staff-policy.test.mjs`) and the page imports them instead of
 *     carrying a second, private copy of the role ladder;
 *   - the page's *wiring* is asserted against its source, because the page is
 *     JSX and this project does not ship a DOM test renderer (the JSX compile
 *     check lives in `next build`, and the structural assertions here are the
 *     ones a browser suite would otherwise cover);
 *   - every string the page asks for exists in **both** locales, so a missing
 *     translation cannot reach the screen as a bare key;
 *   - the two mirrors this project keeps on purpose — `ROLE_LEVEL` against
 *     `backend/common/permissions.py::ROLE_HIERARCHY`, and the capability
 *     labels against `DELEGABLE_CAPABILITIES` — cannot drift silently;
 *   - every endpoint the page calls exists in the backend it calls, and the
 *     create payload's fields exist on the request model that receives them.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DICT } from '../lib/i18n.js';
import { ROLE_LEVEL, CAPABILITY_LABEL_KEYS, ROLE_KEYS } from '../lib/staff-policy.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const REPO = path.resolve(FE, '..');

const PAGE = fs.readFileSync(path.join(FE, 'pages', 'staff.js'), 'utf8');
const POLICY = fs.readFileSync(path.join(FE, 'lib', 'staff-policy.js'), 'utf8');
const PERMISSIONS = fs.readFileSync(
  path.join(REPO, 'backend', 'common', 'permissions.py'), 'utf8');
const IDENTITY_ROUTES = fs.readFileSync(
  path.join(REPO, 'backend', 'identity', 'routes.py'), 'utf8');
const IDENTITY_MAIN = fs.readFileSync(
  path.join(REPO, 'backend', 'identity', 'main.py'), 'utf8');
const IDENTITY_MODELS = fs.readFileSync(
  path.join(REPO, 'backend', 'identity', 'models.py'), 'utf8');
const IDENTITY_API = IDENTITY_ROUTES + '\n' + IDENTITY_MAIN;

/** Every `t('...')` / `t("...")` literal in the page. */
function translationKeys(source) {
  const keys = new Set();
  const re = /\bt\(\s*'([^']+)'\s*\)/g;
  let m;
  while ((m = re.exec(source)) !== null) keys.add(m[1]);
  return [...keys];
}


test('the page offers the shared policy, not a private role ladder', () => {
  for (const name of ['grantableRoles', 'mayGrantCapabilities', 'needsBranch',
    'assignedDoctorIds', 'validateNewStaff', 'staffMatchesFilter',
    'capabilityLabelKey', 'ROLE_KEYS']) {
    assert.match(PAGE, new RegExp('\\b' + name + '\\b'),
      'the page must use ' + name + ' from lib/staff-policy');
  }
  assert.doesNotMatch(PAGE, /const\s+ROLE_LEVEL\s*=/,
    'the role ladder must not be duplicated inside the page');
  assert.doesNotMatch(PAGE, /const\s+ROLE_ORDER\s*=/,
    'the role order must not be duplicated inside the page');
  // The role picker is fed by the policy, never by a hand-written option list.
  assert.match(PAGE, /grantableRoles\(/);
});

test('the roster is read from the endpoint the server serves, per organization', () => {
  assert.match(PAGE, /'\/api\/v1\/staff\/users\?organization_id='/);
  assert.match(PAGE, /'\/api\/v1\/orgs\/' \+ encodeURIComponent\(orgId\) \+ '\/branches'/);
  assert.match(PAGE, /'\/api\/v1\/doctors'/);
});

test('the create form posts the fields the request model accepts', () => {
  const start = IDENTITY_MODELS.indexOf('class StaffUserCreate');
  assert.notEqual(start, -1, 'StaffUserCreate must exist in backend/identity/models.py');
  const rest = IDENTITY_MODELS.slice(start);
  const end = rest.indexOf('\nclass ');
  const model = end === -1 ? rest : rest.slice(0, end);

  const body = PAGE.slice(PAGE.indexOf("await apiFetch('/api/v1/staff/users', {"));
  const jsonStart = body.indexOf('JSON.stringify(');
  // Comments inside the payload explain *why* each field is sent; strip them so
  // only the keys that are actually sent are checked against the model.
  const json = body.slice(jsonStart, body.indexOf('}),', jsonStart))
    .replace(/\/\/[^\n]*/g, '');
  const fields = [...json.matchAll(/([a-z_]+):/g)].map((m) => m[1]);
  assert.ok(fields.includes('username') && fields.includes('password')
    && fields.includes('display_name') && fields.includes('role'),
    'the create payload must carry the identifying fields');
  for (const field of fields) {
    assert.match(model, new RegExp('\\b' + field + '\\b'),
      'StaffUserCreate has no field ' + field);
  }
});

test('the edit path sends only what changed, so no audit row is written for nothing', () => {
  assert.match(PAGE, /method: 'PATCH'/);
  assert.match(PAGE, /const patch = \{\}/,
    'the PATCH body is built by diffing against the last server row');
  assert.match(PAGE, /patch\.display_name =|patch\.branch_id =|patch\.status =/);
  assert.match(PAGE, /'\/api\/v1\/staff\/users\/' \+ editing\.id/);
});

test('deactivation is a two-step action, never a single click', () => {
  assert.match(PAGE, /deactivateConfirm/,
    'the destructive control must ask for confirmation');
  assert.match(PAGE, /activateConfirm/,
    'reactivation carries its own confirmation wording');
  assert.match(PAGE, /data-testid="staff-toggle-status"/);
});

test('a caller cannot change their own role from this screen', () => {
  assert.match(PAGE, /ownRoleLocked/);
  assert.match(PAGE, /disabled=\{isSelf\}[\s\S]{0,120}?data-testid="edit-role"/,
    'the role select must be disabled when the row is the caller');
  assert.match(PAGE, /isSelf=\{editing\.id === user\.id\}/,
    'the dialog is told whether the row is the caller');
});


test('grants are read from the catalogue endpoint, never hard-coded in the page', () => {
  assert.match(PAGE, /'\/api\/v1\/staff\/capabilities'/);
  assert.doesNotMatch(PAGE, /'appointment\.book_cross_branch'/,
    'the delegable set comes from the server, not from a literal list in the page');
  assert.match(PAGE, /'\/api\/v1\/staff\/users\/' \+ editing\.id \+ '\/capabilities'/);
  // Revoking a branch-scoped grant must name the branch, or the row survives.
  assert.match(PAGE, /\?branch_id=' \+ encodeURIComponent\(grantRow\.branch_id\)/);
});

test('the screen is gated on the permission the backend enforces', () => {
  assert.match(PAGE, /can\('staff\.read'\)/);
  assert.match(PAGE, /can\('staff\.manage'\)/);
  assert.match(PAGE, /<PermissionDenied/);
  assert.match(IDENTITY_API, /staff\.read/);
  assert.match(IDENTITY_API, /staff\.manage/);
});

test('every endpoint the page calls is declared by the identity service', () => {
  assert.match(IDENTITY_ROUTES, /\/api\/v1\/staff\/capabilities"/);
  assert.match(IDENTITY_ROUTES, /\/api\/v1\/staff\/users\/\{user_id\}\/capabilities/);
  assert.match(IDENTITY_ROUTES,
    /\/api\/v1\/staff\/users\/\{user_id\}\/capabilities\/\{capability\}/);
  assert.match(IDENTITY_API, /\/api\/v1\/staff\/users"/);
  for (const verb of ['@router.delete', '@router.patch', '@router.post']) {
    assert.match(IDENTITY_API, new RegExp(verb));
  }
});

test('the identifiers a browser suite needs are present', () => {
  const ids = ['staff-new', 'staff-search', 'staff-role-filter', 'staff-status-filter',
    'staff-table', 'staff-create-submit', 'new-username', 'new-password', 'new-role',
    'staff-toggle-status', 'staff-save', 'staff-grants', 'staff-status-confirm',
    'edit-display-name', 'edit-role', 'edit-branch', 'edit-error'];
  for (const id of ids) {
    assert.ok(PAGE.includes('data-testid="' + id + '"'), 'missing testid ' + id);
  }
  for (const id of ["'staff-row-'", "'staff-manage-'", "'staff-grant-'", "'staff-revoke-'",
    "'staff-doctor-'"]) {
    assert.ok(PAGE.includes('data-testid={' + id), 'missing testid ' + id);
  }

test('every translated string the page asks for exists in both locales', () => {
  const keys = translationKeys(PAGE);
  assert.ok(keys.length > 30, 'the page is expected to be fully translated');
  for (const locale of ['bn', 'en']) {
    assert.ok(DICT[locale], 'locale ' + locale + ' must exist');
    for (const key of keys) {
      assert.ok(DICT[locale][key] !== undefined,
        'missing ' + locale + ' translation for "' + key + '"');
    }
  }
});

test('the role and capability labels the policy names are translated too', () => {
  for (const locale of ['bn', 'en']) {
    for (const key of [...Object.values(ROLE_KEYS), 'roleLabel', 'active', 'inactive']) {
      assert.ok(DICT[locale][key] !== undefined,
        'missing ' + locale + ' label for "' + key + '"');
    }
    for (const key of Object.values(CAPABILITY_LABEL_KEYS)) {
      assert.ok(DICT[locale][key] !== undefined,
        'missing ' + locale + ' label for capability "' + key + '"');
    }
  }
});

test('the role ladder mirrors the backend hierarchy exactly', () => {
  const block = PERMISSIONS.slice(PERMISSIONS.indexOf('ROLE_HIERARCHY:'));
  const body = block.slice(0, block.indexOf('}'));
  const backend = {};
  for (const m of body.matchAll(/"([a-z_]+)":\s*(\d+)/g)) backend[m[1]] = Number(m[2]);
  assert.ok(Object.keys(backend).length >= 6);
  assert.deepEqual({ ...ROLE_LEVEL }, backend);
});

test('every delegable capability has a label, and the sets agree', () => {
  const start = PERMISSIONS.indexOf('DELEGABLE_CAPABILITIES');
  const block = PERMISSIONS.slice(start);
  const body = block.slice(0, block.indexOf(')'));
  const delegable = [...body.matchAll(/"([a-z_.]+)"/g)].map((m) => m[1]);
  assert.ok(delegable.length >= 3);
  assert.deepEqual(delegable.slice().sort(), Object.keys(CAPABILITY_LABEL_KEYS).sort(),
    'a capability added on the server must get a label key here');
});

});
