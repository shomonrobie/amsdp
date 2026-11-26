/* MP-39 / MP-45 — the display administration screen.
 *
 * The screen is JSX, so the pure rules live in `lib/displays.js` and are tested
 * directly here; the page is then asserted to *use* those rules rather than
 * carry a second copy, and the backend is asserted to declare the capability,
 * the routes and the audit actions the page relies on.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  EMPTY_DISPLAY, SCOPE_LABEL_KEYS, codeLooksValid, validateDisplayDraft,
  createPayload, patchPayload, displayUrl,
} from '../lib/displays.js';
import { DICT } from '../lib/i18n.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const REPO = path.resolve(FE, '..');

const PAGE = fs.readFileSync(path.join(FE, 'pages', 'queue-displays.js'), 'utf8');
const API = fs.readFileSync(path.join(REPO, 'backend', 'queuing', 'displays.py'), 'utf8');
const PERMISSIONS = fs.readFileSync(
  path.join(REPO, 'backend', 'common', 'permissions.py'), 'utf8');

test('a code is a lower-case handle, and nothing else', () => {
  assert.equal(codeLooksValid('cardio-1'), true);
  assert.equal(codeLooksValid('  CARDIOLOGY  '), true, 'case is normalised, not rejected');
  assert.equal(codeLooksValid('cardio_1'), false, 'an underscore is not a URL handle');
  assert.equal(codeLooksValid('-cardio'), false, 'no leading hyphen');
  assert.equal(codeLooksValid('cardio--one'), false, 'no double hyphen');
  assert.equal(codeLooksValid(''), false);
  assert.equal(codeLooksValid('x'.repeat(41)), false, 'the server caps it at 40');
});

test('the draft is validated before a request is made, in i18n keys', () => {
  assert.equal(validateDisplayDraft({ ...EMPTY_DISPLAY, name: 'A', code: 'a' }).ok, true);
  assert.equal(validateDisplayDraft({ ...EMPTY_DISPLAY, name: '', code: 'a' }).error, 'nameRequired');
  assert.equal(validateDisplayDraft({ ...EMPTY_DISPLAY, name: 'A', code: '' }).error, 'dispCodeHint');
  assert.equal(validateDisplayDraft({
    ...EMPTY_DISPLAY, name: 'A', code: 'a', scope_type: 'department',
  }).error, 'dispDepartmentRequired');
  assert.equal(validateDisplayDraft({
    ...EMPTY_DISPLAY, name: 'A', code: 'a', scope_type: 'room',
  }).error, 'dispRoomRequired');
  assert.equal(validateDisplayDraft({
    ...EMPTY_DISPLAY, name: 'A', code: 'a', scope_type: 'doctors', doctor_ids: [],
  }).error, 'dispSelectDoctors');
  // Every message is a key that exists in both languages, never a sentence.
  for (const key of ['nameRequired', 'dispCodeHint', 'dispDepartmentRequired',
    'dispRoomRequired', 'dispSelectDoctors', 'fillRequired']) {
    assert.ok(DICT.bn[key] !== undefined && DICT.en[key] !== undefined,
      'missing translation for ' + key);
  }
});

test('the create payload sends a target only for the chosen scope', () => {
  const branch = createPayload({ ...EMPTY_DISPLAY, name: ' Hall ', code: 'HALL-1' }, 'br-1');
  assert.equal(branch.branch_id, 'br-1');
  assert.equal(branch.name, 'Hall', 'the name is trimmed');
  assert.equal(branch.code, 'hall-1', 'the code is normalised');
  assert.equal(branch.department_id, null);
  assert.equal(branch.room_id, null);
  assert.deepEqual(branch.doctor_ids, []);

  const room = createPayload({
    ...EMPTY_DISPLAY, name: 'R', code: 'r', scope_type: 'room', room_id: 'room-1',
    department_id: 'stale-dept',
  }, 'br-1');
  assert.equal(room.room_id, 'room-1');
  assert.equal(room.department_id, null,
    'a target that does not belong to the scope is never sent');
});

test('a patch carries only what changed, so no audit row is written for nothing', () => {
  const original = {
    branch_id: 'br-1', name: 'Hall', code: 'hall-1', language: 'bn', scope_type: 'branch',
    department_id: '', room_id: '', footer_text: '', status: 'active',
    show_room: true, show_estimated_wait: true, show_waiting_count: true, doctor_ids: [],
  };
  assert.deepEqual(patchPayload({ ...original }, original), {},
    'an unchanged save sends nothing');
  assert.deepEqual(patchPayload({ ...original, footer_text: 'Welcome' }, original),
    { footer_text: 'Welcome' });
  assert.deepEqual(patchPayload({ ...original, show_room: false }, original),
    { show_room: false });
  const scoped = patchPayload({ ...original, scope_type: 'doctors', doctor_ids: ['d-1'] }, original);
  assert.equal(scoped.scope_type, 'doctors');
  assert.deepEqual(scoped.doctor_ids, ['d-1']);
});

test('the copied URL is the one the public route serves', () => {
  assert.equal(displayUrl('DHK', 'MAIN', 'Cardio-1'),
    '/queue-display/DHK/MAIN?display=cardio-1');
  assert.equal(displayUrl('DHK', 'MAIN', ''), '/queue-display/DHK/MAIN');
});


test('the page offers the shared rules, not a private copy', () => {
  for (const name of ['validateDisplayDraft', 'createPayload', 'patchPayload',
    'displayUrl', 'EMPTY_DISPLAY']) {
    assert.ok(PAGE.indexOf(name) >= 0, 'the page must use ' + name);
  }
  assert.ok(!/const\s+SCOPE_TYPES\s*=/.test(PAGE), 'the scope set is not re-declared');
  assert.ok(!/const\s+L\s*=\s*\{/.test(PAGE), 'no page-local dictionary');
});

test('the screen is gated on the capability the server enforces', () => {
  assert.ok(PAGE.indexOf("can('queue.display.manage')") >= 0);
  assert.ok(PAGE.indexOf('<PermissionDenied') >= 0);
  assert.ok(API.indexOf('DISPLAY_MANAGE = "queue.display.manage"') >= 0);
  // The scope labels the page shows are dictionary keys, not sentences.
  for (const key of Object.values(SCOPE_LABEL_KEYS)) {
    assert.ok(DICT.bn[key] !== undefined && DICT.en[key] !== undefined,
      'missing scope label ' + key);
  }
});

test('the routes and audit actions the page relies on exist on the server', () => {
  assert.ok(API.indexOf('prefix="/api/v1/queue/displays"') >= 0);
  assert.ok(API.indexOf('@router.get("")') >= 0);
  assert.ok(API.indexOf('@router.post("", status_code=201)') >= 0);
  assert.ok(API.indexOf('@router.patch("/{display_id}")') >= 0);
  assert.ok(API.indexOf('CREATED_ACTION = "queue.display.created"') >= 0);
  assert.ok(API.indexOf('UPDATED_ACTION = "queue.display.updated"') >= 0);
  // Before/after is what makes the audit row reviewable.
  assert.ok(API.indexOf('before=before, after=after') >= 0);
  assert.ok(API.indexOf('if before != after:') >= 0,
    'a no-op save must not claim a change');
});

test('MP-46 — a refusal is recorded once, as queue.display.denied', () => {
  assert.ok(API.indexOf('DENIED_ACTION = "queue.display.denied"') >= 0);
  assert.ok(API.indexOf('DOMAIN_DENIAL_HEADER') >= 0,
    'the specific row replaces the generic one, not duplicates it');
  // The organization is never read from the request body.
  assert.ok(API.indexOf('data.organization_id') < 0);
  assert.ok(API.indexOf('Branch.organization_id == auth.organization_id') >= 0);
});

test('MP-39 — the delegable capability set is unchanged and no role was added', () => {
  const start = PERMISSIONS.indexOf('DELEGABLE_CAPABILITIES');
  const body = PERMISSIONS.slice(start, PERMISSIONS.indexOf(')', start));
  const delegable = [...body.matchAll(/"([a-z_.]+)"/g)].map((m) => m[1]);
  assert.deepEqual(delegable.sort(), [
    'appointment.book_cross_branch', 'appointment.check_in',
    'appointment.create_unscheduled',
  ]);
  assert.ok(PERMISSIONS.slice(start).indexOf('queue.display.manage') < 0,
    'display management is not a delegable front-desk capability');
  assert.ok(/"queue\.\*"/.test(PERMISSIONS), 'queue.* still covers queue.display.manage');
});

test('the identifiers a browser suite needs are present', () => {
  for (const id of ['displays-heading', 'displays-branch', 'displays-new', 'displays-list',
    'display-save', 'display-name', 'display-code', 'display-language', 'display-scope',
    'display-footer', 'display-department', 'display-room']) {
    assert.ok(PAGE.indexOf('data-testid="' + id + '"') >= 0, 'missing testid ' + id);
  }
  // The three MP-45 toggles are rendered from one list, so their ids are built.
  assert.ok(PAGE.indexOf("data-testid={'display-' + key}") >= 0, 'missing toggle testids');
  for (const id of ["'display-row-'", "'display-edit-'", "'display-status-'",
    "'display-copy-'", "'display-url-'"]) {
    assert.ok(PAGE.indexOf('data-testid={' + id) >= 0, 'missing testid ' + id);
  }
});
